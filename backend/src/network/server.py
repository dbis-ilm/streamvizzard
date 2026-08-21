from __future__ import annotations
import json
import logging
import threading
import time
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from typing import Dict, Optional

from websockets.sync.server import serve, ServerConnection, Server

from network.commands.commands import Command, CommandRes
from network.commands.debuggerCmds import ChangeDebuggerStateCMD, RequestDebuggerStepCMD, ExecuteProvQueryCMD, \
    ChangeDebuggerConfigCMD, DebuggerStepChange
from network.commands.monitorCmds import ChangeMonitorConfigCMD
from network.commands.pipelineCmds import StartPipelineCMD, StopPipelineCMD, UpdatePipelineCMD, ChangeAdvisorConfigCMD, \
    SimulateCMD
from network.commands.compileCmds import CompileModeStartCMD, CompileAnalyzeCMD, CompileModeEndCMD, CompilePipelineCMD
from network.commands.storageCmds import RetrieveStoredPipelines, RequestStoredPipeline, DeleteStoredPipeline, \
    StorePipeline, RetrieveStoredOperators, DeleteStoredOperator, StoreOperator
from network.socketTuple import SocketTuple
from spe.common.timer import Timer
from streamVizzard import StreamVizzard


class ServerManager:
    def __init__(self, manager: StreamVizzard):
        self.manager = manager

        self.apiServer: Optional[APIServer] = None
        self.socketServer: Optional[WebSocketServer] = None

        self._commandLookup: Dict[str, Command] = dict()

    def start(self, apiPort: int, socketPort: int):
        self._commandLookup = self._setupCommands()

        self.apiServer = APIServer(self, apiPort)
        self.apiServer.startup()

        self.socketServer = WebSocketServer(self, socketPort)
        self.socketServer.startup()

    def shutdown(self):
        if self.socketServer is not None:
            self.socketServer.shutdown()

        if self.apiServer is not None:
            self.apiServer.shutdown()

    def sendSocketData(self, data: SocketTuple | bytes):
        if self.socketServer is None:
            return

        self.socketServer.sendData(data)

    def clearSocketData(self):
        if self.socketServer is None:
            return

        self.socketServer.clearData()

    def flushSocketData(self):
        if self.socketServer is None:
            return

        self.socketServer.flushData()

    def onSocketClosed(self):
        self.manager.stopPipeline()

    def executeCommand(self, name: str, data: Dict, networkMode: NetworkMode) -> Optional[CommandRes]:
        cmd = self._commandLookup.get(name, None)

        if cmd is not None:
            if cmd.networkMode != networkMode:
                return CommandRes.error("Operation not allowed!")

            return cmd.handleCommand(self.manager.runtimeManager, data)

        return None  # Cmd not found

    @staticmethod
    def _setupCommands() -> Dict[str, Command]:
        commandLookup: Dict[str, Command] = dict()

        def _addCmd(cmd: Command):
            commandLookup[cmd.name] = cmd

        # Pipeline
        _addCmd(StartPipelineCMD(NetworkMode.API))
        _addCmd(StopPipelineCMD(NetworkMode.API))
        _addCmd(UpdatePipelineCMD(NetworkMode.SOCKET))  # Includes UI updates

        # Advisor
        _addCmd(ChangeAdvisorConfigCMD(NetworkMode.API))

        # Simulator
        _addCmd(SimulateCMD(NetworkMode.API))

        # Monitor
        _addCmd(ChangeMonitorConfigCMD(NetworkMode.API))

        # Compiler
        _addCmd(CompileAnalyzeCMD(NetworkMode.API))
        _addCmd(CompileModeStartCMD(NetworkMode.API))
        _addCmd(CompileModeEndCMD(NetworkMode.API))
        _addCmd(CompilePipelineCMD(NetworkMode.API))

        # Storage
        _addCmd(RetrieveStoredPipelines(NetworkMode.API))
        _addCmd(RequestStoredPipeline(NetworkMode.API))
        _addCmd(DeleteStoredPipeline(NetworkMode.API))
        _addCmd(StorePipeline(NetworkMode.API))
        _addCmd(RetrieveStoredOperators(NetworkMode.API))
        _addCmd(DeleteStoredOperator(NetworkMode.API))
        _addCmd(StoreOperator(NetworkMode.API))

        # Debugger
        _addCmd(ChangeDebuggerStateCMD(NetworkMode.API))
        _addCmd(ChangeDebuggerConfigCMD(NetworkMode.API))
        _addCmd(RequestDebuggerStepCMD(NetworkMode.API))
        _addCmd(ExecuteProvQueryCMD(NetworkMode.API))
        _addCmd(DebuggerStepChange(NetworkMode.SOCKET))

        return commandLookup


class NetworkMode(Enum):
    SOCKET = "Socket"
    API = "API"


class WebSocketServer:
    def __init__(self, manager: ServerManager, port: int):
        self.manager = manager
        self.running = False

        self.port = port

        self.stopEvent = threading.Event()

        # Disable websocket default logging
        logging.getLogger("websockets").addHandler(logging.NullHandler())
        logging.getLogger("websockets").propagate = False

        self.sendQueue: Queue[SocketTuple | bytes] = Queue(0)

        self._server: Optional[Server] = None
        self._waitEvent = threading.Event()
        self._sendThread = threading.Thread(target=self._sendLoop, daemon=True)

        self.client: Optional[ServerConnection] = None

    def startup(self):
        print("Starting socket (port " + str(self.port) + ")")

        thread = threading.Thread(target=self._threadFunc, daemon=True)
        thread.start()

    def _threadFunc(self):
        self.running = True
        self._sendThread.start()

        with serve(self._handleConnection, "0.0.0.0", self.port, compression=None) as server:
            self._server = server

            server.serve_forever()

        self.stopEvent.set()

    def _handleConnection(self, connection: ServerConnection):
        if self.client is not None:  # Only allow one connection
            return

        self.client = connection

        self.client.send(json.dumps("Connected"))

        print("Client connected")

        while True:
            try:
                data = self.client.recv()
            except Exception:
                print("Client disconnected")

                self.clearData()
                self.client = None

                self.manager.onSocketClosed()

                return

            try:
                jdata = json.loads(data)

                cmd = jdata["cmd"]

                resp = self.manager.executeCommand(cmd, jdata, NetworkMode.SOCKET)

                if resp is not None and resp.resData is not None:
                    self.sendData(resp.resData.encode())  # Potential errors are skipped here (no cmd identifier)
            except Exception:
                ...

    def _sendLoop(self):
        MAX_WAIT_DUR = StreamVizzard.getConfig().NETWORK_MAX_BATCH_DELAY
        MAX_BATCH_SIZE = StreamVizzard.getConfig().NETWORK_MAX_BATCH_SIZE

        while self.running:
            if self.client:
                start = Timer.currentRealTime()

                dataBatch = []  # All individual messages to be sent in this loop
                batchSize = 0

                # Ensure, we don't run into an infinity loop if elm.getData calls take to long (and new messages arrive)
                while self.sendQueue.qsize() > 0 and Timer.currentRealTime() - start < MAX_WAIT_DUR and batchSize < MAX_BATCH_SIZE:
                    elm = self.sendQueue.get(False)

                    data = elm

                    if isinstance(elm, SocketTuple):
                        elm.onSend()

                        data = elm.getData()

                    if data is not None:  # None data (potentially retrieved from SocketTuple:getData) is dropped
                        batchSize += len(data)
                        dataBatch.append(data)

                if len(dataBatch) > 0:
                    dataToSend = b"[" + b",".join(dataBatch) + b"]"  # Res data is an JSON array of individual JSON messages

                    self.client.send(dataToSend, text=True)

                if self.sendQueue.qsize() == 0:
                    self._waitEvent.clear()  # Clear event if no more data

                self._waitEvent.wait()

            time.sleep(0.01)

    def sendData(self, data: SocketTuple | bytes):
        if self.client:
            self.sendQueue.put(data)

            self._waitEvent.set()

    def clearData(self):
        self.sendQueue.queue.clear()

        self._waitEvent.clear()

    def flushData(self):
        # Waits until all data is flushed

        while self.sendQueue.qsize() > 0:
            time.sleep(0.01)

    def shutdown(self):
        print("Stopping socket")

        self.running = False

        if self._server is not None:
            self._server.shutdown()

            self.stopEvent.wait()


class APIServer:
    class ServerHandler(BaseHTTPRequestHandler):
        apiServer: APIServer

        def log_message(self, f: str, *args):
            pass  # Remove logging of http server

        def do_GET(self):
            self._sendResponse(405)  # Not allowed

        def do_OPTIONS(self):
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header("Access-Control-Allow-Headers",
                             "X-Requested-With, Content-type, Access-Control-Allow-Origin")
            self.end_headers()

        def do_POST(self):
            cl = self.headers['Content-Length']

            data = {}

            if cl is not None:
                contentLength = int(cl)
                if contentLength > 0:
                    data = json.loads(self.rfile.read(contentLength))

            commandName = self.path.removeprefix("/")

            resp = self.apiServer.manager.executeCommand(commandName, data, NetworkMode.API)

            content = None

            if resp is None:
                statusCode = 404
            elif resp.hasError():
                statusCode = 400
                content = resp.errorMsg
            elif resp.resData is None:
                statusCode = 204  # No content
            else:
                statusCode = 200
                content = resp.resData

            self._sendResponse(statusCode, content)

        def _sendResponse(self, statusCode: int, content: Optional[str] = None):
            self.send_response(statusCode)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if content is not None:
                self.wfile.write(content.encode('utf-8'))

    def __init__(self, manager: ServerManager, port: int):
        self.running = False
        self.manager = manager

        self.port = port

        self.stopEvent = threading.Event()

        # noinspection PyTypeChecker
        self.server = HTTPServer(('', port), APIServer.ServerHandler)
        APIServer.ServerHandler.apiServer = self

    def startup(self):
        print("Starting api (port " + str(self.port) + ")")

        thread = threading.Thread(target=self._threadFunc, daemon=True)
        thread.start()

    def _threadFunc(self):
        self.running = True

        self.server.serve_forever()

        self.server.server_close()

        self.stopEvent.set()

    def shutdown(self):
        print("Stopping api")

        self.running = False

        self.server.shutdown()

        self.stopEvent.wait()
