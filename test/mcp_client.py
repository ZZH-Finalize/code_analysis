from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool

from typing import Optional

import asyncio
from contextlib import AsyncExitStack

import os

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器

        参数：
            server_script_path: 服务器脚本路径 (.py 或 .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")

        # command = "python" if is_python else "node"
        if os.name == 'nt':
            cmd = 'python'
        elif os.name == 'posix':
            cmd = 'python3.12'
        else:
            raise RuntimeError('env not sup')

        print(f'cmd: {cmd}')

        server_params = StdioServerParameters(
            command=cmd,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # 列出可用工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\n已连接到服务器，可用工具：", [tool.name for tool in tools])

    async def call_tool(self, tool_name, tool_args):
        resp_list = await self.session.call_tool(tool_name, tool_args)
        for resp in resp_list.content:
            print(f'resp: {resp.text}')

    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()

async def main():
    client = MCPClient()

    try:
        if os.name == 'nt':
            await client.connect_to_server('D:/proj/python/code_analysis/code_analysis_mcp.py')
            await client.call_tool('start_analyzer', {
                "workspace_path": "d:/proj/STM32F10x-MesonBuild-Demo"
            })
            await client.call_tool('start_analyzer', {
                "workspace_path": "d:/proj/STM32F10x-MesonBuild-Demo"
            })
            await client.call_tool('add_file', {
                "path_to_file": "src/app/main.c"
            })
            # await client.call_tool('find_all_reference', {
            #     "file": "src/app/main.c",
            #     "symbol_line": '121',
            #     "symbol_column": '19'
            # })
            await client.call_tool('find_all_reference', {
                "symbol_name": "console_update",
            })
        elif os.name == 'posix':
            await client.connect_to_server('/mnt/d/proj/python/code_analysis/code_analysis_mcp.py')
            await client.call_tool('start_analyzer', {
                "workspace_path": "/workspace/proj/baseband/macsw/"
            })
            await client.call_tool('add_file', {
                "path_to_file": "plf/refip/src/arch/risc-v/arch_main.c"
            })
            # await client.call_tool('find_all_reference', {
            #     "file": "/workspace/proj/baseband/macsw/plf/refip/src/arch/risc-v/arch_main.c",
            #     "symbol_line": '34',
            #     "symbol_column": '6'
            # })
            await client.call_tool('find_all_reference', {
                "symbol_name": "rwnx_platform_init",
            })
    finally:
        await client.cleanup()

if '__main__' == __name__:
    asyncio.run(main())
