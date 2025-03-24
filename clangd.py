import subprocess
import json
from packaging import version
import os, sys
import asyncio

class ClangdClient:
    def __init__(self, workspace_dir: str):
        clangd_path = self.__find_clangd()

        print(f'find {clangd_path}')

        self.process = subprocess.Popen(
            executable=clangd_path,
            args=[
                clangd_path,
                '--compile-commands-dir=builddir',
                '--function-arg-placeholders=1',
                '--header-insertion=iwyu',
                '--clang-tidy',
                '--all-scopes-completion',
                '--enable-config',
                '--cross-file-rename',
                # '--background-index',
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workspace_dir,
        )

        # self.response_event = asyncio.Event()
        self.recived_queue = asyncio.Queue()
        self.pending_queue = asyncio.Queue()

        self.id = 10
        self.exit_flag = False

    def exit(self):
        self.exit_flag = True

    def get_id(self):
        self.id = self.id + 1

        if self.id < 0:
            raise RuntimeError('id exhaused !')

        return self.id

    async def recive_task(self):
        while False == self.exit_flag:
            try:
                line = await asyncio.wait_for(asyncio.to_thread(self.process.stdout.readline), timeout=5)
            except asyncio.TimeoutError:
                if self.exit_flag:
                    return
                continue
            print(f'recived resp: {line.removesuffix(b'\r\n')}')

            # is a response instead of a log information
            if line.startswith(b'Content-Length:'):
                # convert length
                length = int(line.split(b':')[1].strip())
                # skip empty line
                self.process.stdout.readline()
                # read remain data
                data = self.process.stdout.read(length).replace(b'\r\n', b'')
                # convert to python dict
                response = json.loads(data)
                # response with id
                if 'id' in response:
                    print(f'resp: {response}')
                    request = await self.pending_queue.get()
                    if request['id'] == response['id']:
                        if 'method' in response:
                            if request['method'] != response['method']:
                                await self.pending_queue.put(request)
                                continue

                        # self.response_event.set()
                        print(f'recive resp for {request['method']}:{request['id']}')
                        await self.recived_queue.put(response)
                    else:
                        print(f'unknow resp for id: {request['id'], response}')
                        await self.pending_queue.put(request)

    async def _send(self, method: str, params: dict, **kwargs):
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        request.update(kwargs)

        message = json.dumps(request)
        req = f'Content-Length: {len(message)}\r\n\r\n{message}'.encode()
        print(f'write a request: {req}')
        self.process.stdin.write(req)
        self.process.stdin.flush()

        if 'id' in kwargs:
            await self.pending_queue.put(request)
            return await self.recived_queue.get()

    async def send_request(self, method: str, params: dict):
        # send request with id
        return await self._send(method, params, id=self.get_id())
    
    async def send_notification(self, method: str, params: dict):
        # send request without id
        await self._send(method, params)

    def __find_clangd(self):
        check_name = 'clangd'
        clangd_abs_path = ''

        if os.name == 'nt':
            check_name = check_name + '.exe'

        for path in os.environ['PATH'].split(';'):
            clangd_abs_path = os.path.join(path, check_name)
            if os.path.exists(clangd_abs_path):
                return clangd_abs_path
            
        # check for vscode
        vscode_ext_dir = ''

        if os.name == 'nt':
            vscode_ext_dir = os.path.join(
                os.environ['USERPROFILE'],
                    'AppData',
                    'Roaming',
                    'Code',
                    'User',
                    'globalStorage',
                    'llvm-vs-code-extensions.vscode-clangd',
                    'install'
                )
        else:
            raise RuntimeError('not support')
            
        if not os.path.exists(vscode_ext_dir):
            return None

        leatest = str(max(map(version.parse, os.listdir(vscode_ext_dir))))
        vscode_clangd = os.path.join(
            vscode_ext_dir,
            leatest,
            'clangd_' + leatest,
            'bin',
            check_name
        )
        
        if os.path.exists(vscode_clangd):
            return vscode_clangd

        return None

# workspace = 'd:/proj/STM32F10x-MesonBuild-Demo'
workspace = 'E:/Shared_Dir/ProgramsAndScripts/embed/C/STM32F10x-MesonBuild-Demo'
client = ClangdClient(workspace)

async def send():
    from init_param import get_init_param
    param = get_init_param()

    print(await client.send_request('initialize', param))
    await client.send_notification('initialized', {})

    file = os.path.join(workspace, 'subprojects/embed-utils/tiny_console/tiny_console.c')
    with open(file) as f:
        await client.send_notification('textDocument/didOpen', {
            'textDocument': {
                'uri': f'file:///{file}',
                # 'uri': f'file:///asdsadsad.c',
                'languageId': 'c',
                'version': 1,
                'text': f.read()
            }
        })

    await asyncio.sleep(5)

    function_name = 'console_send_str'

    print(await client.send_request('workspace/symbol', {
        'query': function_name
    }))

    print(await client.send_request('textDocument/references', {
        'textDocument': {
            'uri': f'file:///{file}'
        },
        "position": {
            "character": 14,
            "line": 146
        },
        "context": {
            "includeDeclaration": True
        }
    }))

    print('program done')

    client.exit()

async def main():
    await asyncio.gather(send(), client.recive_task())

if __name__ == '__main__':
    asyncio.run(main())
