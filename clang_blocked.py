import subprocess
import json
from packaging import version
import os, sys
import queue
import time
from typing import Union
import logging
from urllib.parse import urlparse, unquote
from urllib.request import pathname2url

class ClangdClient:
    def __init__(self, workspace_path: str = ''):
        self.workspace_path = workspace_path
        self.clangd_path = self.__find_clangd()
        self.id = 10
        self.process = None
        self.pending_queue = queue.Queue()
        self.opened_files = set()
        self.script_path = os.path.abspath(os.path.dirname(sys.argv[0]))

        if not os.path.exists(os.path.join(self.script_path, 'logs')):
            os.mkdir(os.path.join(self.script_path, 'logs'))

        time_tag = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())

        self.logger = logging.getLogger(__name__)

        # default disable log
        self.logger.setLevel(logging.CRITICAL)
        for hdlr in self.logger.handlers:
            self.logger.removeHandler(hdlr)

        if len(sys.argv) > 1 and '--enable-log' == sys.argv[1]:
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(logging.FileHandler(os.path.join(self.script_path, 'logs', f'log-{time_tag}.txt'), mode='w'))

        self.logger.info(f'find {self.clangd_path}')

    def _recive(self):
        while True:
            line = self.process.stdout.readline().decode().removesuffix('\r\n')
            self.logger.debug(f'recived resp: {line}')
            # is a response instead of a log information
            if line.startswith('Content-Length:'):
                # convert length
                length = int(line.split(':')[1].strip())
                # skip empty line
                self.process.stdout.readline()
                # read remain data
                data = self.process.stdout.read(length).decode().removesuffix('\r\n')
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
        if None == self.process:
            raise RuntimeError('analyzer is down, please call start_analyzer first')

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
        if '' == workspace_path:
            raise RuntimeError('workspace_path cannot be a empty path')

        if None != self.process and workspace_path != self.workspace_path:
            self.logger.debug('restart server')
            self.stop()

        self.workspace_path = workspace_path
        self.logger.debug('switch to workspace')
        os.chdir(self.workspace_path)

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

        cdb_file = self.__search_cdb()
        cdb_path = os.path.dirname(cdb_file)
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

        with open(os.path.join(self.script_path, 'init_param.json'), encoding='utf-8') as f:
            param = json.loads(f.read())

        self.send_request('initialize', param)
        self.send_notification('initialized', {})
        self.opened_files.clear()

        with open(cdb_file, encoding='utf-8') as f:
            cdb = json.loads(f.read())

        self.did_open(os.path.join(cdb[0]['directory'], cdb[0]['file']))

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

    def check_resault(self, response: dict) -> None:
        if 'error' in response:
            raise RuntimeError(f'error occur: {response['message']}')
        elif [] == response.get('result', []):
            raise RuntimeError('result not found')

    def extract_list(self, response: dict) -> list[str]:
        res = []

        for ref in response['result']:
            rel_path = os.path.relpath(self.uri_to_fn(ref['uri']), self.workspace_path)
            line = ref['range']['start']['line']
            res.append(f'{rel_path}:{line}')

        return res

    def did_open(self, fn: str):
        self.logger.debug(f'fn: {fn}')
        file = os.path.abspath(fn)

        if fn in self.opened_files:
            return file

        with open(file, encoding='utf-8') as f:
            self.send_notification('textDocument/didOpen', {
                'textDocument': {
                    'uri': self.fn_to_uri(file),
                    'languageId': 'c',
                    'version': 1,
                    'text': f.read()
                }
            })

        self.opened_files.add(fn)
        time.sleep(0.5)

    def did_close(self, fn: str):
        file = os.path.abspath(fn)

        self.send_notification('textDocument/didClose', {
            'textDocument': {
                'uri': self.fn_to_uri(file)
            }
        })

        self.opened_files.remove(fn)

    def workspace_symbol(self, symbol: str):
        return self.send_request('workspace/symbol', {
            'query': symbol
        })

    def document_references(self, uri: str, line: int, character: int):
        reference = self.send_request('textDocument/references', {
            'textDocument': {'uri': uri},
            'context': {'includeDeclaration': True},
            'position': {
                'line': int(line),
                'character': int(character)
            },
        })

        self.check_resault(reference)
        return reference

    def document_definition(self, uri: str, line: int, character: int):
        definition = self.send_request('textDocument/definition', {
            'textDocument': {'uri': uri},
            'position': {
                'line': int(line),
                'character': int(character)
            },
        })

        # print(json.dumps(definition, indent=4))

        self.check_resault(definition)
        return definition

    def find_symbol_definition(self, symbol: str):
        symbol_loc = self.locate_symbol(symbol)

        self.did_open(self.uri_to_fn(symbol_loc['uri']))

        definition = self.document_definition(symbol_loc['uri'], **symbol_loc['range']['start'])

        # this means the symbol_loc is the actual definition
        if definition['result'][0]['uri'].endswith('.h'):
            definition = {'result': [symbol_loc]}

        return self.extract_list(definition)

    def find_symbol_in_workspace(self, symbol: str) -> Union[list, str]:
        symbol_loc = self.locate_symbol(symbol)

        self.did_open(self.uri_to_fn(symbol_loc['uri']))

        reference = self.document_references(symbol_loc['uri'], **symbol_loc['range']['start'])

        # self.logger.debug(json.dumps(reference, indent=4))

        return self.extract_list(reference)

    def locate_symbol(self, symbol: str) -> Union[list, str, bool, dict]:
        symbol_resp = self.workspace_symbol(symbol)

        # self.logger.debug(f'symbol_resp: {symbol_resp}')
        # print(json.dumps(symbol_resp, indent=4))
        self.check_resault(symbol_resp)
        return symbol_resp['result'][0]['location']

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

    @staticmethod
    def uri_to_fn(uri: str):
        fn = unquote(urlparse(uri).path)
        if os.name == 'nt':
            fn = fn.removeprefix('/')
        return fn

    @staticmethod
    def fn_to_uri(fn: str):
        return 'file:' + pathname2url(fn)

def send():
    client = ClangdClient()
    client.logger.setLevel(logging.DEBUG)
    workspace = 'd:/proj/STM32F10x-MesonBuild-Demo'
    # workspace = 'E:/Shared_Dir/ProgramsAndScripts/embed/C/STM32F10x-MesonBuild-Demo'

    client.start(workspace)

    # client.did_open('src/app/main.c')

    # sym = client.workspace_symbol('console_update')

    # client.send_request('workspaceSymbol/resolve', sym)

    # for ref_info in client.find_symbol_in_workspace('console_update'):
    #     print(ref_info)

    print(client.find_symbol_definition('console_update'))

    # client.did_close('src/app/main.c')

    time.sleep(2)

    print('program done')

    client.stop()

if __name__ == '__main__':
    send()
