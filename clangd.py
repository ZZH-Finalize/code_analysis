import subprocess
import json
import threading
import queue
import time
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
                '--background-index',
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workspace_dir,
        )

        self.send_queue = queue.Queue()
        self.pending_queue = queue.Queue()
        self.recived_queue = queue.Queue()

        self.id = -1

    def get_id(self):
        self.id = self.id + 1

        if self.id < 0:
            raise RuntimeError('id exhaused !')

        return self.id

    async def _recive_task(self):
        while True:
            # wait until there is data valid
            line = self.process.stdout.readline()
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
                    if not self.pending_queue.empty():
                        request = self.pending_queue.get()
                        print(f'Response for {request['method']}:')
                        # self.recived_queue.put(response)
                        return response

                # response that does not cantain a id
                # print(json.dumps(response, indent=4))

            # handle log information
            else:
                pass
                

    async def recive(self):
        # return await self.recived_queue.get()
        return await self._recive_task()

    async def _send(self, method: str, params: dict, **kwargs):
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        request.update(kwargs)

        if None != kwargs:
            self.pending_queue.put(request)

        message = json.dumps(request)
        req = f'Content-Length: {len(message)}\r\n\r\n{message}'.encode()
        print(f'write a request: {req}')
        self.process.stdin.write(req)
        # print('flush stdin')
        self.process.stdin.flush()

    async def send_request(self, method: str, params: dict):
        # send request with id
        await self._send(method, params, id=self.get_id())
        return await self.recive()
    
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
    

client = ClangdClient('d:/proj/STM32F10x-MesonBuild-Demo')

async def send():
    from init_param import get_init_param
    param = get_init_param()

    print(await client.send_request('initialize', param))
    await client.send_notification('initialized', {})

    file = 'd:/proj/STM32F10x-MesonBuild-Demo/subprojects/embed-utils/tiny_console/tiny_console.c'
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

async def main():
    # await asyncio.gather(send(), client._recive_task())
    await send()

if __name__ == '__main__':
    asyncio.run(main())
