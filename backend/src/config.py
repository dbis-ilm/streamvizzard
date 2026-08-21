from __future__ import annotations


VERSION = "0.9.9"
NETWORKING_SERVER_PORT = 8000
NETWORKING_SOCKET_PORT = 8001


class Config:
    def __init__(self):
        # ----------------------- MISC -----------------------

        self.MISC_PRINT_PIPELINE_ON_START = True

        # --------------------- NETWORK ----------------------

        self.NETWORK_ENABLED = True

        # How long [seconds] the network manager waits at max to bundle packages to transmit
        self.NETWORK_MAX_BATCH_DELAY = 0.1

        # Max batch size [1MB] to reduce latency and avoid huge messages
        self.NETWORK_MAX_BATCH_SIZE = 1024 * 1024

        # --------------------- MONITORING ----------------------

        self.MONITORING_ENABLED = True

        # Time memory for EMA smooth, controls how quickly EMA adapts to new values (full reset after x seconds)
        self.MONITORING_EMA_WINDOW = 2

        # Percentual change to last throughput to trigger adaptive window to more quickly react to changing tps
        self.MONITORING_CONNECTION_WINDOW_THRESHOLD = 5  # Higher=more sensible, Lower=less adaptiveness

        # Required interval [seconds] of the throughput window (adaptive in range [min,max]) for calculation.
        self.MONITORING_CONNECTION_WINDOW_INTERVAL = [0.25, 2.5]  # Higher=less sensible to changes but more robust

        # Required tuples within the throughput window (adaptive in range [min,max]) for calculation.
        self.MONITORING_CONNECTION_WINDOW_COUNT = [5, 25]  # Higher=less sensible to changes but more robust

        # How often the inspection recalculates the data structure of input tuples to verify its integrity
        self.MONITORING_INSPECT_UPDATE_INTERVAL = 5  # Seconds

        # At which rate [seconds] updates to the frontend monitor will be sent
        self.MONITORING_UPDATE_INTERVAL = 0.1

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
