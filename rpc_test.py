import subprocess
import json

class ClangdClient:
    def __init__(self):
        self.process = subprocess.Popen(
            [
                'c:/Users/Siliconwaves_Users/AppData/Roaming/Code/User/globalStorage/llvm-vs-code-extensions.vscode-clangd/install/19.1.2/clangd_19.1.2/bin/clangd.exe',
                "--compile-commands-dir=builddir",
                "--function-arg-placeholders=1",
                "--header-insertion=iwyu",
                "--clang-tidy",
                "--all-scopes-completion",
                "--enable-config",
                "--cross-file-rename",
                "--background-index",
                "--query-driver=D:/SysGCC/arm-none-eabi/bin/arm-none-eabi-gcc"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='d:/proj/STM32F10x-MesonBuild-Demo',
        )
        
    def send_request(self, method, params):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        message = json.dumps(request)
        self.process.stdin.write(f"Content-Length: {len(message)}\r\n\r\n{message}".encode())
        self.process.stdin.flush()
        
    def read_response(self):
        while True:
            line = self.process.stdout.readline()
            if line.startswith(b'Content-Length:'):
                length = int(line.split(b':')[1].strip())
                self.process.stdout.readline()  # Skip empty line
                data = self.process.stdout.read(length)
                return json.loads(data)

def find_function_calls(function_name):
    client = ClangdClient()
    
    # Initialize
    client.send_request("initialize", {
        "processId": None,
        "rootUri": None,
        "capabilities": {
            "textDocument": {
                "didOpen": {
                    "dynamicRegistration": True
                },
                "definition": {
                    "dynamicRegistration": True
                }
            },
            "workspace": {
                "symbol": {
                    "dynamicRegistration": True,
                    "symbolKind": {
                        "valueSet": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
                    }
                }
            }
        }
    })
    print(json.dumps(client.read_response(), indent=4))
    
    # Open document
    client.send_request("textDocument/didOpen", {
        "textDocument": {
            "uri": "file:///subprojects/embed-utils/tiny_console/tiny_console.c",
            "languageId": "c",
            "version": 1,
            "text": ""  # Placeholder for file content
        }
    })
    print(client.read_response())
    
    # Find definition
    client.send_request("textDocument/definition", {
        "textDocument": {
            "uri": "file:///subprojects/embed-utils/tiny_console/tiny_console.c"
        },
        "position": {
            "line": 147,
            "character": 5
        }
    })
    
    response = client.read_response()
    print(response)

    calls = []
    for item in response.get('result', []):
        if function_name in item.get('name', ''):
            calls.append({
                'file': item['location']['uri'],
                'line': item['location']['range']['start']['line']
            })
    return calls

if __name__ == "__main__":
    # Example usage
    calls = find_function_calls("console_send_str")
    if calls:
        print(f"Found {len(calls)} calls to console_send_str:")
        for call in calls:
            print(f"File: {call['file']}, Line: {call['line']}")
    else:
        print("No calls found")
