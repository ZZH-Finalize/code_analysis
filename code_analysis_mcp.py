# from pylsp import LspClient
from mcp.server import Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    ClientCapabilities,
    TextContent,
    Tool,
    ListRootsResult,
    RootsCapability,
)
from typing import Any
from collections.abc import Sequence
from pydantic import BaseModel
import json

server = Server('code-analysis-mcp')

class FindAllReference(BaseModel):
    name: str

    @classmethod
    def exec(cls, name: str) -> list[str]:
        return [
            'main.c:45',
            'caller.cpp:153'
        ]

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name = 'find_all_reference',
            description = 'Find all reference of a function',
            inputSchema = FindAllReference.model_json_schema()
        )
    ]


tool_table = {
    'find_all_reference': FindAllReference
}

@server.call_tool()
async def call_tool(name: str, arg: Any) -> Sequence[TextContent]:
    if name not in tool_table:
        raise ValueError(f'unknow tool: {name}')
    
    resault = tool_table[name].exec(arg)

    return [
        TextContent(
            text = json.dumps(resault),
            type = 'text'
        )
    ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
