# --------------------- OPERATOR MODULES  ---------------------

MODULE_USE_IMAGE_PROCESSING = True

# ----------------------- MISC -----------------------

MISC_PRINT_PIPELINE_ON_START = True

# --------------------- NETWORK ----------------------

NETWORKING_SERVER_PORT = 3000  # If changed, also adapt Frontend
NETWORKING_SOCKET_PORT = 3001  # If changed, also adapt Frontend

# How many elements can be scheduled in the send queue at most, None if infinite
NETWORKING_SOCKET_SEND_QUEUE_CAPACITY = 200

# --------------------- MONITORING ----------------------

MONITORING_ENABLED = True

# How many data entries will be considered when calculating statistics for an operator
MONITORING_OPERATOR_MAX_TUPLES = 50

# At which rate [seconds] updates to the frontend monitor will be sent
MONITORING_UPDATE_INTERVAL = 0.1

# How many elements of history are considered to calc statistics
# This influences how quickly changes in throughput are noticeable
MONITORING_CONNECTIONS_MAX_THROUGHPUT_ELEMENTS = 10

# --------------------- PIPELINE DEBUGGER ----------------------

DEBUGGER_ENABLED = True

# If the time of the steps should not be used how many steps per second should be processed at 1x speed
DEBUGGER_HISTORY_REWIND_BASE_STEP_FREQUENCY = 25

DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_MEM_SIZE = 10000000  # [10MB] In bytes
DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_TUP_COUNT = 25  # The more tup the more steps need to be removed at once when freeing mem

# --------------------- DEBUGGER PROVENANCE ----------------------

DEBUGGER_PROV_INSPECTOR_ENABLED = False

DEBUGGER_PROV_DOCKER_SOCKET = "npipe:////./pipe/docker_engine"  # (windows) | unix:///run/user/1000/docker.sock for linux

DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD = 0.2  # Percentage of change for Con TP/ Op EX times to trigger a new metric node
DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD = 10  # Absolute of change for MQ Size to trigger a new metric ndoe
