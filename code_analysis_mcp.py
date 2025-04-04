# from pylsp import LspClient
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, GetPromptResult, PromptMessage, Prompt
from typing import Any
from collections.abc import Sequence
import json

from tools import tool_list

server = Server('code-analysis-mcp')

tool_table = {}

@server.list_tools()
async def list_tools() -> list[Tool]:
    tool_register_list: list[Tool] = []

    for tool in tool_list:
        tool_register_list.append(Tool(
            name = tool.__name__,
            description = tool.__doc__,
            inputSchema = tool.model_json_schema()
        ))

    return tool_register_list

@server.call_tool()
async def call_tool(name: str, arg: Any) -> Sequence[TextContent]:
    if name not in tool_table:
        raise ValueError(f'unknow tool: {name}')

    resault = await tool_table[name].exec(arg)

    if None == resault:
        resault = True

    return [
        TextContent(
            text = json.dumps(resault),
            type = 'text'
        )
    ]

# @server.get_prompt()
# async def get_prompt(name: str, arg: dict[str, str] | None) -> GetPromptResult:
#     return GetPromptResult(description='desc', messages=[
#         PromptMessage(
#             role="user",
#             content=TextContent(
#                 text=f'input name: {name}, input arg: {arg}',
#                 type='text'
#             )
#         )
#     ])

# @server.list_prompts()
# async def list_prompts() -> list[Prompt]:
#     return [
#         Prompt(
#             name='analysis',
#             description='first desc',
#         )
#     ]

async def main():
    global tool_table

    for tool in tool_list:
        tool_table.update({tool.__name__: tool})

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == '__main__':
    import asyncio
    # print(f'model_json_schema: {tool_list[0].model_json_schema()}')
    asyncio.run(main())
