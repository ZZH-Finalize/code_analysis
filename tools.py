from pydantic import BaseModel, Field
from functools import wraps
from typing import Callable
from clang_blocked import ClangdClient

client = ClangdClient()


# accept original function
def unwrap_arg(fun: Callable) -> Callable:
    # accept original function args
    @wraps(fun)
    def wrapper(args: dict):
        # unwrap arg here
        import inspect

        arg_list = []

        sign = inspect.signature(fun)

        for name, _ in sign.parameters.items():
            arg_list.append(args[name])

        return fun(*arg_list)
    return wrapper

class start_analyzer(BaseModel):
    """Start the code analyzer in a workspace"""
    workspace_path: str = Field(description='absolute path to the current workspace')

    @unwrap_arg
    @staticmethod
    def exec(workspace_path):
        client.start(workspace_path)

class stop_analyzer(BaseModel):
    """Stop the code analyzer"""

    @unwrap_arg
    @staticmethod
    def exec():
        client.stop()

class find_definition(BaseModel):
    """Find definition position of a symbol"""
    symbol_name: str = Field(description='function name or variable name')

    @unwrap_arg
    @staticmethod
    def exec(symbol_name: str) -> list[str]:
        return client.find_symbol_definition(symbol_name)

class find_all_reference(BaseModel):
    """Find all reference of a symbol"""
    symbol_name: str = Field(description='function name or variable name')

    @unwrap_arg
    @staticmethod
    def exec(symbol_name: str) -> list[str]:
        return client.find_symbol_references(symbol_name)


tool_list: list[BaseModel] = [
    start_analyzer,
    stop_analyzer,
    find_definition,
    find_all_reference,
]
