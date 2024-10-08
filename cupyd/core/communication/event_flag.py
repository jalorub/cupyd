from abc import abstractmethod
from multiprocessing import Event as MPEvent
from threading import Event as ThreadingEvent


class EventFlag:
    """This communication mechanism will be used to transmit actions to specific ETL Nodes."""

    @abstractmethod
    def __bool__(self) -> bool:
        """Indicate if the event is True or False."""
        pass

    @abstractmethod
    def wait(self):
        """If the event is enabled, wait till its set to False."""
        pass

    @abstractmethod
    def set(self):
        """Activate the event by setting it to True."""
        pass


class InterProcessEventFlag(EventFlag):

    def __init__(self, start_set: bool = False):
        self._event = MPEvent()
        if not start_set:
            self._event.set()

    def __bool__(self) -> bool:
        return not self._event.is_set()

    def wait(self):
        self._event.wait()

    def set(self):
        if self:
            self._event.set()
        else:
            self._event.clear()


class IntraProcessEventFlag(EventFlag):

    def __init__(self):
        self._event = ThreadingEvent()
        self._event.set()

    def __bool__(self) -> bool:
        return not self._event.is_set()

    def wait(self):
        self._event.wait()

    def set(self):
        if self:
            self._event.set()
        else:
            self._event.clear()
