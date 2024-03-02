from streamVizzard import StreamVizzard
import atexit


systemInstance = StreamVizzard


def shutdown():
    systemInstance.shutdown()


atexit.register(shutdown)

if __name__ == '__main__':
    systemInstance = StreamVizzard()
    systemInstance.startUp()

