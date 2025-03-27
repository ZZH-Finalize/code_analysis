from pydantic import BaseModel, Field
from functools import wraps
from typing import Callable
from clang_blocked import ClangdClient

client = ClangdClient()

# accept argument from decorator
def unwrap_arg(*arg_keys) -> Callable:
    # accept original function
    def decorator(fun: Callable) -> Callable:
        # accept original function args
        def wrapper(args: dict):
            # unwrap arg here
            arg_list = []

            for arg_key in arg_keys:
                arg_list.append(args[arg_key])

            return fun(*arg_list)
        return wrapper
    return decorator

class Test(BaseModel):
    """MCP server测试API, 直接返回传入的参数"""
    arg_a: str
    arg_b: str

    """
    testing prompt: 使用123和456作为参数调用CodeAnalysis里的test工具
    """

    @staticmethod
    def get_name() -> str:
        return 'test'

    @unwrap_arg('arg_a', 'arg_b')
    @staticmethod
    def exec(a: str, b: str) -> list[str]:
        return [
            f'arg_a: {a}',
            f'arg_b: {b}',
        ]

class Env(BaseModel):
    """read envirement"""

    @staticmethod
    def get_name() -> str:
        return 'env'

    @unwrap_arg()
    @staticmethod
    def exec() -> list[str]:
        import sys
        return [
            sys.argv,
        ]
    
class start_analyzer(BaseModel):
    """Start the code analyzer in a workspace"""
    workspace_path: str = Field(description='absolute path to the current workspace')
    
    @unwrap_arg('workspace_path')
    @staticmethod
    def exec(path):
        client.start(path)

class stop_analyzer(BaseModel):
    """Stop the code analyzer"""
    
    @unwrap_arg()
    @staticmethod
    def exec():
        client.stop()

class find_definition(BaseModel):
    """Find definition position of a symbol"""
    symbol_name: str = Field(description='function name or variable name')

    @unwrap_arg('symbol_name')
    @staticmethod
    def exec(symbol_name: str) -> list[str]:
        return client.find_symbol_definition(symbol_name)

class find_all_reference(BaseModel):
    """Find all reference of a symbol"""
    symbol_name: str = Field(description='function name or variable name')

    @unwrap_arg('symbol_name')
    @staticmethod
    def exec(symbol_name: str) -> list[str]:
        return client.find_symbol_in_workspace(symbol_name)


tool_list: list[BaseModel] = [
    start_analyzer,
    stop_analyzer,
    find_definition,
    find_all_reference,

    # Test,
    # Env,
]
