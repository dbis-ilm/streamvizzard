from __future__ import annotations
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from typing import Dict, Optional, TYPE_CHECKING

from websockets.sync.server import serve, ServerConnection, WebSocketServer as WebSocketServerImpl

from network.commands.commands import Command
from network.commands.debuggerCmds import ChangeDebuggerStateCMD, RequestDebuggerStepCMD, ExecuteProvQueryCMD, \
    ChangeDebuggerConfigCMD, DebuggerStepChange
from network.commands.monitorCmds import ChangeMonitorConfigCMD
from network.commands.pipelineCmds import StartPipelineCMD, StopPipelineCMD, UpdatePipelineCMD, ChangeAdvisorConfigCMD, \
    SimulateCMD
from network.commands.compileCmds import CompileModeStartCMD, CompileAnalyzeCMD, CompileModeEndCMD, CompilePipelineCMD
from network.commands.storageCmds import RetrieveStoredPipelines, RequestStoredPipeline, DeleteStoredPipeline, \
    StorePipeline, RetrieveStoredOperators, DeleteStoredOperator, StoreOperator

if TYPE_CHECKING:
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

    def sendSocketData(self, data):
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

    # TODO: Restrict api/socket access to commands + return StatusCode on api!
    def executeCommand(self, name: str, data) -> Optional[str]:
        cmd = self._commandLookup.get(name, None)

        if cmd is not None:
            return cmd.handleCommand(self.manager.runtimeManager, data)

        return None

    @staticmethod
    def _setupCommands() -> Dict[str, Command]:
        commandLookup:  Dict[str, Command] = dict()

        def _addCmd(cmd: Command):
            commandLookup[cmd.name] = cmd

        _addCmd(StartPipelineCMD())
        _addCmd(StopPipelineCMD())
        _addCmd(UpdatePipelineCMD())
        _addCmd(ChangeAdvisorConfigCMD())
        _addCmd(SimulateCMD())

        _addCmd(ChangeMonitorConfigCMD())

        _addCmd(CompileAnalyzeCMD())
        _addCmd(CompileModeStartCMD())
        _addCmd(CompileModeEndCMD())
        _addCmd(CompilePipelineCMD())

        _addCmd(RetrieveStoredPipelines())
        _addCmd(RequestStoredPipeline())
        _addCmd(DeleteStoredPipeline())
        _addCmd(StorePipeline())
        _addCmd(RetrieveStoredOperators())
        _addCmd(DeleteStoredOperator())
        _addCmd(StoreOperator())

        _addCmd(ChangeDebuggerStateCMD())
        _addCmd(ChangeDebuggerConfigCMD())
        _addCmd(RequestDebuggerStepCMD())
        _addCmd(ExecuteProvQueryCMD())
        _addCmd(DebuggerStepChange())

        return commandLookup


class WebSocketServer:
    def __init__(self, manager: ServerManager, port: int):
        self.manager = manager
        self.running = False

        self.port = port

        self.stopEvent = threading.Event()

        # Disable websocket default logging
        logging.getLogger("websockets").addHandler(logging.NullHandler())
        logging.getLogger("websockets").propagate = False

        self.sendQueue = Queue(0)

        self._server: Optional[WebSocketServerImpl] = None
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

        with serve(self._handleConnection, "0.0.0.0", self.port) as server:
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

                resp = self.manager.executeCommand(cmd, jdata)

                if resp is not None:
                    self.sendData(resp)
            except Exception:
                ...

    def _sendLoop(self):
        from network.socketTuple import SocketTuple

        while self.running:
            if self.client:
                while self.sendQueue.qsize() > 0:  # TODO: COULD BE PACKED INTO ONE MESSAGE
                    elm = self.sendQueue.get(False)

                    data = elm

                    if isinstance(elm, SocketTuple):
                        elm.onSend()

                        data = elm.getData()

                    if data is not None:
                        self.client.send(data)

                self._waitEvent.wait()

            time.sleep(0.01)

    def sendData(self, data):
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

        def log_message(self, f: str,  *args):
            pass  # Remove logging of http server

        def do_GET(self):
            self._sendResponse()

        def do_OPTIONS(self):
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type, Access-Control-Allow-Origin")
            self.end_headers()

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])

            data = None

            if content_length > 0:
                data = json.loads(self.rfile.read(content_length))

            commandName = self.path.removeprefix("/")

            resp = self.apiServer.manager.executeCommand(commandName, data)

            self._sendResponse(resp)

        def _sendResponse(self, content: Optional[str] = None):
            self.send_response(200)
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
