import json
import logging
import socket
import traceback
from typing import Optional

from spe.pipeline.operators.source import Source


class SocketServer(Source):
    def __init__(self,  opID: int):
        super(SocketServer, self).__init__(opID, 0, 1)

        self.port = 0
        self.ip = ""
        self.maxBytes = 0

        self._socket: Optional[socket.socket] = None
        self._connection = None

    def setData(self, data: json):
        ipOrPortChanged = (self.port != data["port"]) or (self.ip != data["ip"])

        self.port = data["port"]
        self.ip = data["ip"]
        self.maxBytes = data["maxBytes"]

        if ipOrPortChanged:
            self._close()

    def getData(self) -> dict:
        return {"port": self.port, "ip": self.ip, "maxBytes": self.maxBytes}

    def onRuntimeDestroy(self):
        super(SocketServer, self).onRuntimeDestroy()

        self._close()

    def _close(self):
        try:
            if self._connection is not None:
                self._connection.close()

                self._connection = None

            if self._socket is not None:
                self._socket.close()

                self._socket = None
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def _runSource(self):
        while self.isRunning():
            self._socket = socket.socket()
            self._socket.bind((self.ip, self.port))
            self._socket.listen(1)

            try:
                self._connection, address = self._socket.accept()
            except:  # In case the socket is closed, and we do not have a connection yet
                ...

            while self._connection is not None:
                try:
                    data = self._connection.recv(self.maxBytes)

                    if not data:
                        self._connection.close()

                        break

                    self._produce((data,))
                except Exception as e:
                    # logging.log(logging.ERROR, traceback.format_exc())

                    break

        self._close()
