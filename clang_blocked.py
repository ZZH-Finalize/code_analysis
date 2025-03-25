import subprocess
import json
from packaging import version
import os, sys
import queue
import time
from typing import Union
import logging

class ClangdClient:
    def __init__(self, workspace_path: str = ''):
        self.workspace_path = workspace_path
        self.clangd_path = self.__find_clangd()
        self.id = 10
        self.process = None
        self.pending_queue = queue.Queue()
        self.opened_files = set()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler('/mnt/d/proj/python/code_analysis/log.txt', mode='w'))
        self.logger.info(f'find {self.clangd_path}')

    def _recive(self):
        while True:
            line = self.process.stdout.readline()
            self.logger.debug(f'recived resp: {line.removesuffix(b'\r\n')}')
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
                    self.logger.debug(f'resp: {response}')
                    request = self.pending_queue.get()
                    if request['id'] == response['id']:
                        if 'method' in response:
                            if request['method'] != response['method']:
                                self.pending_queue.put(request)
                                continue

                        # self.response_event.set()
                        self.logger.debug(f'recive resp for {request['method']}:{request['id']}')
                        return response
                    else:
                        self.logger.debug(f'unknow resp for id: {request['id'], response}')
                        self.pending_queue.put(request)

    def _send(self, method: str, params: dict, **kwargs):
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        request.update(kwargs)

        message = json.dumps(request)
        req = f'Content-Length: {len(message)}\r\n\r\n{message}'.encode()
        self.logger.debug(f'write a request: {req}')
        self.process.stdin.write(req)
        self.process.stdin.flush()

        if 'id' in kwargs:
            self.pending_queue.put(request)
            return self._recive()
        
    def get_id(self):
        self.id = self.id + 1

        if self.id < 0:
            raise RuntimeError('id exhaused !')

        return self.id

    def start(self, workspace_path: str = ''):
        if '' != workspace_path:
            self.workspace_path = workspace_path

        if None != self.process:
            return 'analyzer already running, please stop and re-start'
        
        clangd_args = [
                self.clangd_path,
                '--function-arg-placeholders=1',
                '--header-insertion=iwyu',
                '--clang-tidy',
                '--all-scopes-completion',
                '--enable-config',
                '--cross-file-rename',
                # '--log=verbose',
                # '--background-index',
            ]
        
        cdb_path = os.path.dirname(self.__search_cdb())
        self.logger.debug(f'cdb_path: {cdb_path}')
        clangd_args.append(f'--compile-commands-dir={cdb_path}')
        if None == cdb_path:
            raise RuntimeError('no compile_commands.json found')

        self.process = subprocess.Popen(
            executable=self.clangd_path,
            args=clangd_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.workspace_path,
        )

        from init_param import get_init_param
        param = get_init_param()
        self.send_request('initialize', param)
        self.send_notification('initialized', {})
        self.opened_files.clear()
    
    def stop(self):
        self.process.terminate()
        self.process = None
        self.workspace_path = ''
        self.opened_files.clear()

    def send_request(self, method: str, params: dict):
        # send request with id
        return self._send(method, params, id=self.get_id())
    
    def send_notification(self, method: str, params: dict):
        # send request without id
        self._send(method, params)

    def check_resault(self, response: dict) -> Union[list, str, bool]:
        if None == response.get('result', None):
            return []
        elif 'error' in response:
            return response['message']
        else:
            return True
    
    def did_open(self, fn: str):
        if fn in self.opened_files:
            return

        if os.path.exists(fn):
            file = fn
        else:
            file = os.path.join(self.workspace_path, fn)

        with open(file, encoding='utf-8') as f:
            self.send_notification('textDocument/didOpen', {
                'textDocument': {
                    'uri': f'file:///{file}',
                    'languageId': 'c',
                    'version': 1,
                    'text': f.read()
                }
            })

        self.opened_files.add(fn)

        time.sleep(10)
    
    def did_close(self, fn: str):
        if fn not in self.opened_files:
            return

        if os.path.exists(fn):
            file = fn
        else:
            file = os.path.join(self.workspace_path, fn)

        self.send_notification('textDocument/didClose', {
            'textDocument': {
                'uri': f'file:///{file}'
            }
        })

        self.opened_files.remove(fn)

    def workspace_symbol(self, symbol: str):
        return self.send_request('workspace/symbol', {
            'query': symbol
        })

    def document_references(self, uri: str, line: int, character: int):
        return self.send_request('textDocument/references', {
            'textDocument': {'uri': uri},
            'context': {'includeDeclaration': True},
            'position': {
                'line': line,
                'character': character
            },
        })

    def find_symbol_in_workspace(self, symbol: str) -> Union[list, str]:
        symbol_resp = self.workspace_symbol(symbol)

        # self.logger.debug(f'symbol_resp: {symbol_resp}')

        fail_res = self.check_resault(symbol_resp)
        if fail_res is not True:
            return fail_res

        symbol_loc = symbol_resp['result'][0]['location']
        reference = self.document_references(symbol_loc['uri'], **symbol_loc['range']['start'])

        # self.logger.debug(f'reference: {reference}')

        fail_res = self.check_resault(reference)
        if fail_res is not True:
            return fail_res

        # self.logger.debug(json.dumps(reference, indent=4))

        ref_list = []

        for ref in reference['result']:
            rel_path = os.path.relpath(ref['uri'].removeprefix('file:///'), self.workspace_path)
            line = ref['range']['start']['line']
            ref_list.append(f'{rel_path}:{line}')

        return ref_list

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
        elif os.name == 'posix':
            vscode_ext_dir = os.path.join(
                os.path.expanduser('~'),
                    '.vscode-server',
                    'data',
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
    
    def __search_cdb(self):
        import fnmatch
        for root, dir, files in os.walk(self.workspace_path):
            # print(f'root: {root}, _:{dir}, files: {files}')
            for file_path in fnmatch.filter(files, 'compile_commands.json'):
                return os.path.relpath(os.path.join(root, file_path), self.workspace_path)
        return None

def send():
    client = ClangdClient()
    client.logger.setLevel(logging.DEBUG)
    workspace = 'd:/proj/STM32F10x-MesonBuild-Demo'
    # workspace = 'E:/Shared_Dir/ProgramsAndScripts/embed/C/STM32F10x-MesonBuild-Demo'

    client.start(workspace)

    client.did_open('d:/proj/STM32F10x-MesonBuild-Demo/src/app/main.c')

    for ref_info in client.find_symbol_in_workspace('main'):
        print(ref_info)

    client.did_close('d:/proj/STM32F10x-MesonBuild-Demo/src/app/main.c')

    time.sleep(2)

    print('program done')

    client.stop()

if __name__ == '__main__':
    send()
