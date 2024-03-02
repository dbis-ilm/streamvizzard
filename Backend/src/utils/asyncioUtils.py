import asyncio
from time import sleep as ex_sleep


async def windowsAsyncSleep(sleepDuration: float) -> None:
    # A more accurate asyncio.sleep variant for Windows systems which use 15ms clock resolution
    # and are not able to sleep for durations less than the clock res

    # https://textual.textualize.io/blog/2022/12/30/a-better-asyncio-sleep-for-windows-to-fix-animation/

    await asyncio.get_running_loop().run_in_executor(None, ex_sleep, sleepDuration)
