from __future__ import annotations


NETWORKING_SERVER_PORT = 8000
NETWORKING_SOCKET_PORT = 8001


class Config:
    def __init__(self):
        # ----------------------- MISC -----------------------

        self.MISC_PRINT_PIPELINE_ON_START = True

        # --------------------- NETWORK ----------------------

        self.NETWORK_ENABLED = True

        # --------------------- MONITORING ----------------------

        self.MONITORING_ENABLED = True

        # Smooth factor [0,1] when calculating statistics for an operator [Exponential Moving Average] (0=low impact of new values)
        self.MONITORING_OPERATOR_SMOOTH_FACTOR = 2 / (40 + 1)

        # At which rate [seconds] updates to the frontend monitor will be sent
        self.MONITORING_UPDATE_INTERVAL = 0.1

        # How many elements of history are considered to calc statistics
        # This influences how quickly changes in throughput are noticeable
        self.MONITORING_CONNECTIONS_MAX_THROUGHPUT_ELEMENTS = 50

        self.MONITORING_TRACK_PIPELINE_STATS = True

        # ------------------------- ADVISOR --------------------------

        self.ADVISOR_ENABLED = True

        # At which rate [seconds] the advisorStrategies will make a suggestion
        self.ADVISOR_FREQUENCY = 2

        # --------------------- PIPELINE DEBUGGER ----------------------

        self.DEBUGGER_ENABLED = True

        # If the time of the steps should not be used how many steps per second should be processed at 1x speed
        self.DEBUGGER_HISTORY_REWIND_BASE_STEP_FREQUENCY = 25

        self.DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_MEM_SIZE = 10000000  # [10MB] In bytes
        self.DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_TUP_COUNT = 25  # The more tup the more steps need to be removed at once when freeing mem

        # --------------------- DEBUGGER PROVENANCE ----------------------

        self.DEBUGGER_PROV_INSPECTOR_ENABLED = False

        self.DEBUGGER_PROV_DOCKER_SOCKET = "npipe:////./pipe/docker_engine"  # unix:///run/user/1000/docker.sock for linux

        self.DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD = 0.25  # Percentage of change for Con TP/ Op EX times to trigger a new metric node
        self.DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD = 50  # Absolute of change for MQ Size to trigger a new metric node

        # --------------------- PIPELINE COMPILER ----------------------

        self.COMPILER_ENABLED = True

        self.COMPILER_CODE_GEN_DISCLAIMER = "|--------------------------------------------------------|\n| This code was generated automatically by StreamVizzard.|\n|--------------------------------------------------------|"

    @staticmethod
    def getRuntimeOnly() -> Config:
        """ Disables all development functionalities but keeps the networking to control the system. """

        config = Config()

        config.MONITORING_ENABLED = False
        config.DEBUGGER_ENABLED = False
        config.ADVISOR_ENABLED = False
        config.COMPILER_ENABLED = False

        return config
