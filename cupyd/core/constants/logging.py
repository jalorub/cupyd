PINK = "\033[95m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END = "\033[0m"

LOGGING_FORMAT = "%(asctime)-28s" "%(name)-26s" "%(levelname)-12s" "%(message)s"
LOGGING_FORMAT_W_NODE_NAME = (
    "%(asctime)-28s" f"{BOLD}%(threadName)-20s{END}" "%(name)-26s" "%(levelname)-12s" "%(message)s"
)

LOGGING_MSG_PADDING = f"{'':>64}"
