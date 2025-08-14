import functools
from typing import Callable, Awaitable

from utils.messages import Messages


def debugMethod(dm: Callable[..., Awaitable[bool]]):
    def decorator(function):
        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            operator = args[0]

            if operator.__class__.__name__ == "MessageBroker":
                operator = operator._operator

            # Execute debug function
            if operator.isDebuggingEnabled(False):
                if operator.isDebuggingSupported():
                    execute = await dm(*args, **kwargs)  # Returns true if pipeline is continued

                    if not execute:
                        return None  # Continuation, no execution of original method
                else:
                    operator.onExecutionError(Messages.DEBUGGER_OP_NOT_SUPPORTED.value)

            if not operator.isRunning():
                return None

            # Execute original function
            result = await function(*args, **kwargs)

            return result

        return wrapper

    return decorator
