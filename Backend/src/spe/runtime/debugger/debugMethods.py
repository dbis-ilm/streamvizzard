import functools
from typing import Callable, Awaitable, Optional

from spe.runtime.debugger.debugStep import DebugStep


def debugMethod(dm: Callable[..., Awaitable[Optional[DebugStep]]]):
    def decorator(function):
        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            operator = args[0]

            if operator.__class__.__name__ == "MessageBroker":
                operator = operator._operator
            # Execute debug function
            if operator.isDebuggingEnabled(False):
                if operator.isDebuggingSupported():
                    res = await dm(*args, **kwargs)  # Returns continuation step if pipeline is continued

                    if res is not None:
                        return res  # Continuation, no execution of original method
                else:
                    operator.onExecutionError("Operator does not support debugging!")

            # Execute original function
            result = await function(*args, **kwargs)

            return result

        return wrapper

    return decorator
