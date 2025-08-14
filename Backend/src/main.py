import argparse
import signal

from config import Config
from streamVizzard import StreamVizzard
import atexit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Starts the StreamVizzard system with optional configurations.")
    parser.add_argument("--runtimeOnly", action="store_true", help="Starts the system in runtime only mode, omitting "
                                                                   "all development functionality such as the monitor or debugger.")

    args = parser.parse_args()

    if args.runtimeOnly:
        print("Configured StreamVizzard in RuntimeOnly mode!")

    systemInstance = StreamVizzard(Config.getRuntimeOnly() if args.runtimeOnly else Config())
    systemInstance.start()

    atexit.register(systemInstance.shutdown)
    signal.signal(signal.SIGTERM, lambda signum, frame: systemInstance.shutdown())

    systemInstance.keepRunning()

    systemInstance.shutdown()
