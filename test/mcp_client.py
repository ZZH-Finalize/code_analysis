from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool

from typing import Optional

import asyncio
from contextlib import AsyncExitStack

import os, sys

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
            args=[server_script_path, '--enable-log'],
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

test_cases = {
    'nt': [
        ('start_analyzer', {"workspace_path": "D:/proj/STM32F10x-MesonBuild-Demo"}),
        ('start_analyzer', {"workspace_path": "D:/proj/STM32F10x-MesonBuild-Demo"}),
        ('find_all_reference', {"symbol_name": "console_update"}),
        ('find_all_reference', {"symbol_name": "console_send_str"}),
        ('find_definition', {"symbol_name": "console_update"}),
        ('find_definition', {"symbol_name": "map_search"}),
        ('find_definition', {"symbol_name": "main"}),
    ],
    'posix': [
        ('start_analyzer', {"workspace_path": "/workspace/proj/baseband/macsw/"}),
        ('find_all_reference', {"symbol_name": "rwnx_platform_init"}),
        ('find_definition', {"symbol_name": "rxl_mpdu_isr"}),
    ]
}

async def main():
    client = MCPClient()

    try:
        script_path = os.path.dirname(sys.argv[0])
        await client.connect_to_server(os.path.join(script_path, '..', 'code_analysis_mcp.py'))

        for tool, param in test_cases[os.name]:
            await client.call_tool(tool, param)

    finally:
        await client.cleanup()

if '__main__' == __name__:
    asyncio.run(main())
