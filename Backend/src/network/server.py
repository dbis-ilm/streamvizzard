import json
import logging
import threading
import time
import traceback
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from typing import Callable, Optional

from websockets.sync.server import serve, ServerConnection, WebSocketServer as WebSocketServerImpl

from config import NETWORKING_SOCKET_SEND_QUEUE_CAPACITY
from utils.utils import printWarning


class ReceiveType(Enum):
    START_PIPELINE = 1
    UPDATE_PIPELINE = 2
    STOP_PIPELINE = 3
    CHANGE_HEATMAP = 5
    COMPILE = 6
    TOGGLE_ADVISOR = 7
    CHANGE_DEBUGGER_STATE = 8
    CHANGE_DEBUGGER_CONFIG = 9,
    CHANGE_DEBUGGER_STEP = 11,
    REQUEST_DEBUGGER_STEP = 12,
    SIMULATE = 10


class ServerManager:
    httpd = HTTPServer
    apiPort = int
    socketPort = int
    running = bool

    def __init__(self):
        self.manager = None

        logging.getLogger("websockets").addHandler(logging.NullHandler())
        logging.getLogger("websockets").propagate = False

        self.apiThread = threading.Thread(target=self._apiThreadFunc, daemon=True)
        self.socketThread = threading.Thread(target=self._socketThreadFunc)
        self.websocket: Optional[WebSocketServer] = None

    def start(self, port, socketPort, manager):
        self.apiPort = port
        self.socketPort = socketPort
        self.manager = manager

        server_address = ('', port)
        self.httpd = HTTPServer(server_address, Server)

        self.httpd.RequestHandlerClass.serverManager = self

        self.apiThread.start()

        self.socketThread.start()

        return self.apiThread, self.socketThread

    def shutdown(self):
        if self.websocket is not None:
            self.websocket.shutdown()

        self.running = False

    def sendSocketData(self, data):
        self.websocket.sendData(data)

    def clearSocketData(self):
        self.websocket.clearData()

    def _apiThreadFunc(self):
        print("Starting server at port " + str(self.apiPort))
        self.running = True

        while self.running:
            try:
                self.httpd.handle_request()
            except KeyboardInterrupt:
                pass

        self.httpd.server_close()

        print("Stopping server")

    def _socketThreadFunc(self):
        print("Starting socket at port " + str(self.socketPort))

        self.websocket = WebSocketServer(self.handleReceivedData, self.onSocketClosed)
        self.websocket.startup(self.socketPort)

        print("Stopping socket")

    def handleReceivedData(self, receiveType: ReceiveType, data: json):
        try:  # TODO: LOOKUP
            if receiveType == ReceiveType.START_PIPELINE:
                self.manager.onPipelineStart(data)
            elif receiveType == ReceiveType.UPDATE_PIPELINE:
                self.manager.onPipelineUpdated(data)
            elif receiveType == ReceiveType.STOP_PIPELINE:
                self.manager.onPipelineStop(data)
            elif receiveType == ReceiveType.CHANGE_HEATMAP:
                self.manager.onHeatmapChanged(data)
            elif receiveType == ReceiveType.COMPILE:
                self.manager.compilePipeline(data)
            elif receiveType == ReceiveType.SIMULATE:
                self.manager.simulatePipeline(data)
            elif receiveType == ReceiveType.TOGGLE_ADVISOR:
                self.manager.onAdvisorToggled(data)
            elif receiveType == ReceiveType.CHANGE_DEBUGGER_STATE:
                self.manager.onDebuggerStateChanged(data)
            elif receiveType == ReceiveType.CHANGE_DEBUGGER_CONFIG:
                self.manager.onDebuggerConfigChanged(data)
            elif receiveType == ReceiveType.CHANGE_DEBUGGER_STEP:
                self.manager.onDebuggerStepChange(data)
            elif receiveType == ReceiveType.REQUEST_DEBUGGER_STEP:
                self.manager.onDebuggerRequestStep(data)

        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def onSocketClosed(self):
        self.manager.onPipelineStop(None)


class WebSocketServer:
    def __init__(self, onHandleData: Callable, onSocketClosed: Callable):
        self.running = False

        self.onHandleData = onHandleData
        self.onSocketClosed = onSocketClosed

        self.sendQueue = Queue(0)
        self.maxQueueSize = NETWORKING_SOCKET_SEND_QUEUE_CAPACITY

        self._server: Optional[WebSocketServerImpl] = None
        self._waitEvent = threading.Event()
        self._sendThread = threading.Thread(target=self._sendLoop, daemon=True)

        self.client: Optional[ServerConnection] = None

    def startup(self, port):
        self.running = True
        self._sendThread.start()

        with serve(self._handleConnection, "localhost", port) as server:
            self._server = server

            server.serve_forever()

    def _handleConnection(self, connection: ServerConnection):
        if self.client is not None:  # Only allow one connection
            return

        self.client = connection

        self.client.send(json.dumps("Connected"))

        print("Client connected")

        while True:
            try:
                data = self.client.recv()

                # print("received: " + data)
            except:
                print("Client disconnected")

                self.clearData()
                self.client = None

                self.onSocketClosed()

                return

            try:
                jdata = json.loads(data)

                cmdType: Optional[ReceiveType] = None

                cmd = jdata["cmd"]

                if cmd == "pipelineUpdate":
                    cmdType = ReceiveType.UPDATE_PIPELINE
                elif cmd == "debuggerStepChange":
                    cmdType = ReceiveType.CHANGE_DEBUGGER_STEP

                if cmdType is not None:
                    self.onHandleData(cmdType, jdata)
            except:
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

            if self.maxQueueSize is not None and self.sendQueue.qsize() > self.maxQueueSize:
                self.sendQueue.get(False)  # Pop oldest element to make space for new element

                printWarning("Socket connection to slow, we are dropping packages! Results on UI might be incorrect!")

            self._waitEvent.set()

    def clearData(self):
        self.sendQueue.queue.clear()

        self._waitEvent.clear()

    def shutdown(self):
        self.running = False

        self._server.shutdown()


class Server(BaseHTTPRequestHandler):
    serverManager = ServerManager

    def log_message(self, f: str,  *args):
        pass  # Remove logging of http server

    def _set_response(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        self._set_response()
        # self.wfile.write("{'res': 'Ok'}".encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type, Access-Control-Allow-Origin")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data

        data = self.rfile.read(content_length)

        # post_data = self.rfile.read(content_length) # <--- Gets the data itself
        post_data = json.loads(data)

        receiveType = ReceiveType

        if self.path == "/startPipeline":
            receiveType = ReceiveType.START_PIPELINE
        elif self.path == "/stopPipeline":
            receiveType = ReceiveType.STOP_PIPELINE
        elif self.path == "/changeHeatmap":
            receiveType = ReceiveType.CHANGE_HEATMAP
        elif self.path == "/compile":
            receiveType = ReceiveType.COMPILE
        elif self.path == "/simulate":
            receiveType = ReceiveType.SIMULATE
        elif self.path == "/toggleAdvisor":
            receiveType = ReceiveType.TOGGLE_ADVISOR
        elif self.path == "/changeDebuggerState":
            receiveType = ReceiveType.CHANGE_DEBUGGER_STATE
        elif self.path == "/changeDebuggerConfig":
            receiveType = ReceiveType.CHANGE_DEBUGGER_CONFIG
        elif self.path == "/requestDebuggerStep":
            receiveType = ReceiveType.REQUEST_DEBUGGER_STEP

        self._set_response()

        self.serverManager.handleReceivedData(receiveType, post_data)
