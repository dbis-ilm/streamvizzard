import logging
import socket
import traceback
from typing import Optional, Callable, Dict

from spe.pipeline.operators.source import Source


class SocketServer(Source):
    def __init__(self,  opID: int):
        super(SocketServer, self).__init__(opID, 0, 1)

        self._socket = SocketServerImpl()

    def setData(self, data: Dict):
        ipOrPortChanged = (self._socket.port != data["port"]) or (self._socket.ip != data["ip"])

        self._socket.port = data["port"]
        self._socket.ip = data["ip"]
        self._socket.maxBytes = data["maxBytes"]

        if ipOrPortChanged:
            self._socket.close()

    def getData(self) -> dict:
        return {"port": self._socket.port, "ip": self._socket.ip, "maxBytes": self._socket.maxBytes}

    def onRuntimeDestroy(self):
        super(SocketServer, self).onRuntimeDestroy()

        self._socket.close()

    def _runSource(self):
        while self.isRunning():
            self._socket.ensureConnection()

            # Loop until client disconnects
            self._socket.receiveData(self._onDataReceived)

        self._socket.close()

    def _onDataReceived(self, data: bytes):
        self._produce((data,))


class SocketServerImpl:
    # Only accepts one client connection!

    def __init__(self):
        self.port = 0
        self.ip = ""
        self.maxBytes = 0

        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None

    def ensureConnection(self):
        # Creates the socket and awaits a client connection

        if self.socket is None:
            self.socket = socket.socket()
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            self.socket.listen(1)

        if self.connection is not None:
            return

        try:
            self.connection, address = self.socket.accept()
        except OSError:  # In case the socket is closed, and we do not have a connection yet
            pass
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def receiveData(self, receiveCallback: Callable[[bytes], None]):
        while self.connection is not None:
            try:
                data = self.connection.recv(self.maxBytes)

                if not data:
                    break

                receiveCallback(data)
            except ConnectionError:
                break
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

                break

        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def writeData(self, data: bytes):
        if self.connection is not None:
            try:
                self.connection.sendall(data)
            except ConnectionError:
                self.connection.close()
                self.connection = None
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

                self.connection.close()
                self.connection = None

    def close(self):
        try:
            if self.connection is not None:
                self.connection.close()

                self.connection = None

            if self.socket is not None:
                self.socket.close()

                self.socket = None
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def hasConnection(self) -> bool:
        return self.connection is not None
