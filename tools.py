from pydantic import BaseModel
from functools import wraps
from typing import Callable

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

class FindAllReference(BaseModel):
    """Find all reference of a symbol"""
    symbol_name: str

    @staticmethod
    def get_name() -> str:
        return 'find_all_reference'

    @unwrap_arg('symbol_name')
    @staticmethod
    def exec(symbol_name: str) -> list[str]:
        return [
            'main.c:45',
            'caller.cpp:153'
        ]



tool_list = [
    FindAllReference,
    Test
]
