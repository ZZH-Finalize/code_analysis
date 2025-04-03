from collections import deque
from typing import Union

import json
import os, sys
import asyncio
import logging
import time
import clangd_utils

class ClangdClient:
    def __init__(self, workspace_path: str = ''):
        self.workspace_path = workspace_path
        self.id = 10
        self.process: clangd_utils.subprocess.Popen = None
        self.opened_files = set()
        self.script_path = os.path.abspath(os.path.dirname(sys.argv[0]))

        # requests or notifications that wait to be send
        self.send_queue = asyncio.Queue()
        # requests that wait for ack
        self.pending_queue = deque()

        # recived response queue
        self.recived_queue = asyncio.Queue()
        # clangd started flag
        self.clangd_started = asyncio.Event()
        # compile database loaded flag
        self.cdb_loaded = asyncio.Event()

        if not os.path.exists(os.path.join(self.script_path, 'logs')):
            os.mkdir(os.path.join(self.script_path, 'logs'))

        time_tag = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())

        self.logger = logging.getLogger(__name__)

        # default disable log
        self.logger.setLevel(logging.CRITICAL)
        for hdlr in self.logger.handlers:
            self.logger.removeHandler(hdlr)

        if len(sys.argv) > 1 and '--enable-log' == sys.argv[1]:
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(logging.FileHandler(os.path.join(self.script_path, 'logs', f'log-{time_tag}.txt'), mode='w'))

    def __done_cb(self, task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError as e:
            self.logger.info(f'task: {task.get_name()} canceled')
        except Exception as e:
            asyncio.get_event_loop().stop()
            raise e

    async def __recive_task(self):
        while True:
            # clangd should be started before read any messages
            await self.clangd_started.wait()

            # wait for a line is read in buffer            
            line: bytes = await asyncio.to_thread(self.process.stdout.readline)
            line: str = line.decode().removeprefix('\r\n')

            # is a response instead of a log information
            if line.startswith('Content-Length:'):
                # convert length
                length = int(line.split(':')[1].strip())
                # skip empty line
                self.process.stdout.readline()
                # read remain data
                data = self.process.stdout.read(length).decode().removesuffix('\r\n')
                # convert to python dict
                response: dict = json.loads(data)
                # response with id
                if 'id' in response:
                    self.logger.debug(f'resp: {response}')

                    # there is no pending requests
                    if 0 == len(self.pending_queue):
                        # skip this response
                        continue

                    # peek the first request in the pending_requests list
                    request = self.pending_queue[0]

                    # id unmatched
                    if request['id'] != request['id']:
                        self.logger.info(f'unknow resp for id: {request['id']}')
                        continue

                    if 'method' in response:
                        if request['method'] != response['method']:
                            self.logger.info(f'unknow resp for: {response['method']}({request['id']})')
                            continue

                    self.logger.info(f'recive resp for {request['method']}({request['id']})')
                    # put response to the recived queue
                    await self.recived_queue.put(response)
                    # remove the corresponding request
                    self.pending_queue.popleft()
                # no id in response
                else:
                    self.logger.info(f'recived no id msg: {response}')
            # not started with Content-Length, might be a log information
            else:
                self.logger.debug(f'recived log: {line.removesuffix('\r\n')}')

    async def __send_task(self):
        while True:
            # clangd should be started before read any messages
            await self.clangd_started.wait()
            # wait for send queue data avalible
            request = await self.send_queue.get()
            # convert dict to json string
            message = json.dumps(request)
            # add message header
            req = f'Content-Length: {len(message)}\r\n\r\n{message}'.encode()

            log_info = f'write a message: {request['method']}'
            # request with id means this is a request instead of a notification
            if 'id' in request:
                log_info += f'({request['id']})'
                # put request into pending queue waitting for response
                self.pending_queue.append(request)
            self.logger.info(log_info)

            # write formated message and flush write buffer
            await asyncio.to_thread(self.process.stdin.write, req)
            await asyncio.to_thread(self.process.stdin.flush)

    async def _send(self, method: str, params: dict, **kwargs):
        if not self.clangd_started.is_set():
            raise RuntimeError('analyzer is down, please call start_analyzer first')

        # make request body
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        request.update(kwargs)

        # put request to sending queue
        await self.send_queue.put(request)

    def get_id(self):
        self.id = self.id + 1

        if self.id < 0:
            raise RuntimeError('id exhaused !')

        return self.id

    async def start(self, workspace_path: str = ''):
        if '' == workspace_path:
            raise RuntimeError('workspace_path cannot be a empty path')

        # if process started and workspace changed 
        if None != self.process and workspace_path != self.workspace_path:
            self.logger.info('restart server')
            # restart server
            await self.stop()

        # process cwd
        self.workspace_path = workspace_path
        self.logger.info(f'os cwd switch to {workspace_path}')
        os.chdir(self.workspace_path)

        # launch clangd process
        self.process, cdb_file, clangd_path = clangd_utils.create_clangd_process(self.workspace_path)
        self.logger.info(f'find clangd: {clangd_path}')

        # set clangd start flag
        self.clangd_started.set()

        # start running recive task
        self.recive_task = asyncio.create_task(self.__recive_task(), name='recive_task')
        self.send_task = asyncio.create_task(self.__send_task(), name='send_task')

        self.recive_task.add_done_callback(self.__done_cb)
        self.send_task.add_done_callback(self.__done_cb)

        # load init param
        with open(os.path.join(self.script_path, 'init_param.json'), encoding='utf-8') as f:
            param = json.loads(f.read())

        # perform initialize sequence
        await self.send_request('initialize', param)
        await self.send_notification('initialized', {})

        # find a random file from cdb
        with open(cdb_file, encoding='utf-8') as f:
            cdb = json.loads(f.read())

        # send did open request to force clangd load cdb
        await self.did_open(os.path.join(cdb[0]['directory'], cdb[0]['file']))

    async def stop(self):
        self.recive_task.cancel()
        self.send_task.cancel()

        self.process.terminate()
        self.process = None
        self.workspace_path = ''
        self.opened_files.clear()

        # clear queues
        self.send_queue = asyncio.Queue()
        self.pending_queue.clear()
        self.recived_queue = asyncio.Queue()

        # clear flags
        self.clangd_started.clear()
        self.cdb_loaded.clear()

    async def send_request(self, method: str, params: dict):
        # send request with id
        await self._send(method, params, id=self.get_id())

        # wait for response
        return await self.recived_queue.get()

    async def send_notification(self, method: str, params: dict):
        # send request without id
        await self._send(method, params)

    async def did_open(self, fn: str):
        file = os.path.abspath(fn)

        # if this file already opened
        if fn in self.opened_files:
            # skip it
            return file

        with open(file, encoding='utf-8') as f:
            await self.send_notification('textDocument/didOpen', {
                'textDocument': {
                    'uri': clangd_utils.fn_to_uri(file),
                    'languageId': 'c',
                    'version': 1,
                    'text': f.read()
                }
            })

        # record opened file
        self.opened_files.add(fn)
        # todo: use self.cdb_loaded flag
        await asyncio.sleep(5)

        return file

    async def did_close(self, fn: str):
        file = os.path.abspath(fn)

        await self.send_notification('textDocument/didClose', {
            'textDocument': {
                'uri': clangd_utils.fn_to_uri(file)
            }
        })

        self.opened_files.remove(fn)

    async def workspace_symbol(self, symbol: str):
        return await self.send_request('workspace/symbol', {
            'query': symbol
        })

    async def document_references(self, uri: str, line: int, character: int):
        reference = await self.send_request('textDocument/references', {
            'textDocument': {'uri': uri},
            'context': {'includeDeclaration': True},
            'position': {
                'line': int(line),
                'character': int(character)
            },
        })

        clangd_utils.check_resault(reference)
        return reference

    async def document_definition(self, uri: str, line: int, character: int):
        definition = await self.send_request('textDocument/definition', {
            'textDocument': {'uri': uri},
            'position': {
                'line': int(line),
                'character': int(character)
            },
        })

        clangd_utils.check_resault(definition)
        return definition

    async def find_symbol_definition(self, symbol: str):
        # find symbol location first
        symbol_loc = await self.locate_symbol(symbol)
        # open the file which symbol at
        await self.did_open(clangd_utils.uri_to_fn(symbol_loc['uri']))

        # find symbol definition
        definition = await self.document_definition(symbol_loc['uri'], **symbol_loc['range']['start'])

        # this means the symbol_loc is the actual definition
        if definition['result'][0]['uri'].endswith('.h'):
            definition = {'result': [symbol_loc]}

        return clangd_utils.extract_list(definition, self.workspace_path)

    async def find_symbol_references(self, symbol: str) -> Union[list, str]:
        # find symbol location first
        symbol_loc = await self.locate_symbol(symbol)
        # open the file which symbol at
        await self.did_open(clangd_utils.uri_to_fn(symbol_loc['uri']))

        # find symbol references
        reference = await self.document_references(symbol_loc['uri'], **symbol_loc['range']['start'])

        # self.logger.debug(json.dumps(reference, indent=4))

        return clangd_utils.extract_list(reference, self.workspace_path)

    async def locate_symbol(self, symbol: str) -> Union[list, str, bool, dict]:
        symbol_resp = await self.workspace_symbol(symbol)

        # self.logger.debug(f'symbol_resp: {symbol_resp}')
        # print(json.dumps(symbol_resp, indent=4))
        clangd_utils.check_resault(symbol_resp)
        return symbol_resp['result'][0]['location']


async def main():
    client = ClangdClient()
    workspace = 'd:/proj/STM32F10x-MesonBuild-Demo'
    # workspace = 'E:/Shared_Dir/ProgramsAndScripts/embed/C/STM32F10x-MesonBuild-Demo'

    await client.start(workspace)

    print('clangd started')

    # client.did_open('src/app/main.c')

    # sym = client.workspace_symbol('console_update')

    # client.send_request('workspaceSymbol/resolve', sym)

    # for ref_info in client.find_symbol_in_workspace('console_update'):
    #     print(ref_info)

    print(await client.find_symbol_definition('console_update'))

    # client.did_close('src/app/main.c')

    await client.stop()


    await client.start(workspace)
    print('clangd restarted')
    print(await client.find_symbol_definition('console_update'))
    await client.stop()

    print('program done')

if __name__ == '__main__':
    asyncio.run(main())
