import ctypes
import logging
import signal
from multiprocessing import Lock, Value

from data_etl.core.communication.event_flag import InterProcessEventFlag

logger = logging.getLogger('data_etl.interrupt')


class InterruptionHandler:
    """Class responsible for setting up a handler for termination signals, in order to perform
    clean shutdowns of running ETLs."""

    def __init__(self, stop_event: InterProcessEventFlag):
        self._lock = Lock()
        self._stop_event = stop_event
        self._interrupted = Value(ctypes.c_bool, False)

    def start(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        try:
            signal.signal(signal.SIGQUIT, self._handle_signal)
            signal.signal(signal.SIGHUP, self._handle_signal)
        except AttributeError:
            pass

    def interrupted(self) -> bool:
        with self._lock:
            return self._interrupted.value

    def _handle_signal(self, *_):
        with self._lock:
            interrupted = self._interrupted.value
            if not interrupted:
                logger.warning('Interruption signal detected, stopping the ETL...')
                self._interrupted.value = True
                if not self._stop_event:
                    self._stop_event.set()
