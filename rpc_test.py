import subprocess
import json
import threading
import queue
import time

class ClangdClient:
    def __init__(self):
        self.process = subprocess.Popen(
            executable='c:/Users/Siliconwaves_Users/AppData/Roaming/Code/User/globalStorage/llvm-vs-code-extensions.vscode-clangd/install/19.1.2/clangd_19.1.2/bin/clangd.exe',
            args=[
                'c:/Users/Siliconwaves_Users/AppData/Roaming/Code/User/globalStorage/llvm-vs-code-extensions.vscode-clangd/install/19.1.2/clangd_19.1.2/bin/clangd.exe',
                '--compile-commands-dir=builddir',
                '--function-arg-placeholders=1',
                '--header-insertion=iwyu',
                '--clang-tidy',
                '--all-scopes-completion',
                '--enable-config',
                '--cross-file-rename',
                '--background-index',
                # '--log=verbose',
                '--query-driver=D:/SysGCC/arm-none-eabi/bin/arm-none-eabi-gcc'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd='d:/proj/STM32F10x-MesonBuild-Demo',
        )
        self.send_queue = queue.Queue()
        self.pending_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.sender_thread = threading.Thread(target=self._sender_loop)
        self.receiver_thread = threading.Thread(target=self._receiver_loop)
        self.sender_thread.start()
        self.receiver_thread.start()
        self.id = -1

        time.sleep(1)

    def get_id(self):
        self.id = self.id + 1
        return self.id
        
    def _sender_loop(self):
        while not self.stop_event.is_set():
            while not self.pending_queue.empty():
                pass

            if self.send_queue.empty():
                continue

            print('fetch a request')

            try:
                method, params, need_rsp = self.send_queue.get(timeout=0.1)
                if need_rsp:
                    print(f'push to pending: {method}')
                    self.pending_queue.put(method)
                self._send_request(method, params, has_id=need_rsp)
            finally:
                pass
        
    def _receiver_loop(self):
        while not self.stop_event.is_set():
            line = self.process.stdout.readline()
            print(f'recived resp: {line.removesuffix(b'\r\n')}')
            if line.startswith(b'Content-Length:'):
                length = int(line.split(b':')[1].strip())
                self.process.stdout.readline()  # 跳过空行
                data = self.process.stdout.read(length).replace(b'\r\n', b'')
                response = json.loads(data)
                if 'id' in response:
                    if not self.pending_queue.empty():
                        method = self.pending_queue.get()
                        print(f'Response for {method}:')
                print(json.dumps(response, indent=4))

    def _send_request(self, method, params, has_id):
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        if True == has_id:
            request.update({'id': self.get_id()})

        message = json.dumps(request)
        req = f'Content-Length: {len(message)}\r\n\r\n{message}'.encode()
        print(f'write a request: {req}')
        self.process.stdin.write(req)
        # print('flush stdin')
        self.process.stdin.flush()
        
    def send_request(self, method, params, need_rsp=True):
        print(f'push a request: {method}')
        self.send_queue.put((method, params, need_rsp))
        
    def close(self):
        self.stop_event.set()
        self.sender_thread.join()
        self.receiver_thread.join()
        self.process.terminate()

def find_function_calls(function_name):
    client = ClangdClient()

    from init_param import get_init_param
    param = get_init_param()

    used_param = {
        'locale': 'zh-cn',
        # 'processId': 6156,
        'rootPath': 'd:\\proj\\STM32F10x-MesonBuild-Demo',
        'rootUri': 'file:///d%3A/proj/STM32F10x-MesonBuild-Demo',
        'trace': 'off',
        'workspaceFolders': [
            {
                'name': 'STM32F10x-MesonBuild-Demo',
                'uri': 'file:///d%3A/proj/STM32F10x-MesonBuild-Demo'
            }
        ],
        'capabilities': {
            'textDocument': {
                'didOpen': {
                    'dynamicRegistration': True
                },
                'didChange': {
                    'syncKind': 1
                },
                'didClose': {
                    'documentSelector': None
                },
                'declaration': {
                    'dynamicRegistration': True,
                    'linkSupport': True
                },
                'definition': {
                    'dynamicRegistration': True,
                    'linkSupport': True
                },
            },
            'workspace': {
                "configuration": True,
                'symbol': {
                    'dynamicRegistration': True,
                    'resolveSupport': {
                        'properties': [
                            'location.range'
                        ]
                    },
                    'symbolKind': {
                        'valueSet': [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23,
                            24,
                            25,
                            26
                        ]
                    },
                    'tagSupport': {
                        'valueSet': [
                            1
                        ]
                    }
                },
            }
        }
    }

    # used_param.update(param['capabilities'])

    # Initialize
    client.send_request('initialize', used_param)
    # client.send_request('initialize', param)
    client.send_request('initialized', {}, False)

    file = 'd:/proj/STM32F10x-MesonBuild-Demo/subprojects/embed-utils/tiny_console/tiny_console.c'

    # Open document
    with open(file) as f:
        client.send_request('textDocument/didOpen', {
            'textDocument': {
                'uri': f'file:///{file}',
                # 'uri': f'file:///asdsadsad.c',
                'languageId': 'c',
                'version': 1,
                'text': f.read()
            }
        }, False)

    time.sleep(5)

    client.send_request('workspace/symbol', {
        'query': function_name
    })

    # client.send_request('workspace/semanticTokens/refresh', None)
    
    # Find definition
    client.send_request('textDocument/references', {
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
    })


if __name__ == '__main__':
    find_function_calls('console_send_str')

