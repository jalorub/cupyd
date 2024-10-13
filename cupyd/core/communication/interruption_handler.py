import ctypes
import logging
import signal
from multiprocessing import Lock, Value
from typing import Dict, Union, Callable, no_type_check

from cupyd.core.communication.event_flag import InterProcessEventFlag

logger = logging.getLogger("cupyd.interrupt")


class InterruptionHandler:
    """Class responsible for setting up a handler for termination signals, in order to perform
    clean shutdowns of running ETLs."""

    def __init__(self, stop_event: InterProcessEventFlag):
        self._lock = Lock()
        self._stop_event = stop_event
        self._interrupted = Value(ctypes.c_bool, False)
        self._original_signal_handlers: Dict[int, Union[Callable, int]] = {}

    @no_type_check
    def start(self):
        self._original_signal_handlers[signal.SIGINT] = signal.signal(
            signal.SIGINT, self._handle_signal
        )
        self._original_signal_handlers[signal.SIGTERM] = signal.signal(
            signal.SIGTERM, self._handle_signal
        )
        try:
            self._original_signal_handlers[signal.SIGQUIT] = signal.signal(
                signal.SIGQUIT, self._handle_signal
            )
            self._original_signal_handlers[signal.SIGHUP] = signal.signal(
                signal.SIGHUP, self._handle_signal
            )
        except AttributeError:
            pass

    def interrupted(self) -> bool:
        with self._lock:
            return self._interrupted.value

    def _handle_signal(self, *_):
        with self._lock:
            interrupted = self._interrupted.value
            if not interrupted:
                logger.warning("Interruption signal detected, stopping the ETL...")
                self._interrupted.value = True
                if not self._stop_event:
                    self._stop_event.set()

    def restore_handlers(self):
        for signal_, original_signal_handler in self._original_signal_handlers.items():
            signal.signal(signal_, original_signal_handler)
