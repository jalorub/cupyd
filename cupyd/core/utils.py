import contextlib
import logging
from datetime import timedelta
from typing import List, Tuple, Optional
from typing import Union, Dict, Iterable

from cupyd.core.constants.logging import LOGGING_FORMAT_W_NODE_NAME

root_logger = logging.getLogger()


def format_seconds(seconds: Union[int, float]) -> str:
    return str(timedelta(seconds=seconds))


def get_subdict(dictionary: Dict, keys: Iterable[str]) -> Dict:
    return {key: dictionary[key] for key in keys if key in dictionary}


@contextlib.contextmanager
def use_cupyd_logging_format(logging_format: str = LOGGING_FORMAT_W_NODE_NAME):
    original_formatters: List[Tuple[logging.Handler, logging.Formatter]] = []
    original_level: Optional[int] = None

    try:
        # store original formatters for all handlers of the root logger
        for handler in root_logger.handlers:
            original_formatters.append((handler, handler.formatter))
            handler.setFormatter(logging.Formatter(logging_format))
        yield

    finally:
        # restore original formatters
        for handler, formatter in original_formatters:
            handler.setFormatter(formatter)

        # restore original level
        if original_level is not None:
            root_logger.setLevel(original_level)
