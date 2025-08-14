import json
import logging
import socket
import traceback
from typing import Optional, Callable

from spe.pipeline.operators.source import Source


class SocketServer(Source):
    def __init__(self,  opID: int):
        super(SocketServer, self).__init__(opID, 0, 1)

        self._socket = SocketServerImpl()

    def setData(self, data: json):
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
            self._socket.awaitConnection()

            self._socket.receiveData(self._onDataReceived)

        self._socket.close()

    def _onDataReceived(self, data: bytes):
        self._produce((data,))


class SocketServerImpl:
    def __init__(self):
        self.port = 0
        self.ip = ""
        self.maxBytes = 0

        self.socket: Optional[socket.socket] = None
        self.connection = None

    def awaitConnection(self):
        # Creates the socket and awaits a client connection

        self.socket = socket.socket()
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)

        try:
            self.connection, address = self.socket.accept()
        except:  # In case the socket is closed, and we do not have a connection yet
            ...

    def receiveData(self, receiveCallback: Callable[[bytes], None]):
        while self.connection is not None:
            try:
                data = self.connection.recv(self.maxBytes)

                if not data:
                    self.connection.close()

                    break

                receiveCallback(data)
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

                break

    def writeData(self, data: bytes):
        if self.connection is not None:
            try:
                self.connection.send(data)
            except ConnectionAbortedError:
                self.connection = None
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

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
