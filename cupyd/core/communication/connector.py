import logging
import multiprocessing
import queue
from abc import abstractmethod
from copy import deepcopy
from typing import Optional, Any, List

from _multiprocessing import SemLock

from cupyd.core.constants.sentinel_values import NO_MORE_ITEMS

logger = logging.getLogger("cupyd.connector")


class Connector:
    """Unidirectional connection mechanism between two Nodes.

    There are 2 possible types of Connector based on where both Nodes exist. Each Connector type
    will use its own communication mechanism to share items between the two Nodes.

    These are the available Connector types:

    1) IntraProcess Connector
        * Nodes run at the same Process.
        * Communication mechanism: queue.Queue
        * Optional: can choose a maxsize for its internal queue.

    2) InterProcess Connector
        * Nodes run in different Processes from same computer.
        * Communication mechanism: multiprocessing.Queue
        * Optional: can choose a maxsize for its internal queue.

    TODO 3) Distributed Connector
        * Nodes run in different Processes from different computers.
        * Communication mechanism: TCP Socket
    """

    def __init__(self, maxsize: Optional[int] = 0):
        super().__init__()
        self._maxsize = maxsize
        self._started = False

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def produce(self, bucket: List[Any]):
        pass

    @abstractmethod
    def consume(self) -> Optional[List[Any]]:
        pass

    @abstractmethod
    def finish_producing(self, num_consumers: int):
        pass

    @abstractmethod
    def get_current_size(self) -> int:
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    def started(self) -> bool:
        return self._started


class IntraProcessConnector(Connector):
    """Used for communication between Nodes at the same process pool where threading is used."""

    def __init__(self, maxsize: Optional[int] = 0):
        super().__init__(maxsize=maxsize)
        self.copy_bucket_on_produce: bool = False
        self._queue: Optional[queue.Queue] = None

    def start(self):
        self._queue = queue.Queue(maxsize=self._maxsize)
        self._started = True

    def produce(self, bucket: List[Any]):
        if self.copy_bucket_on_produce:
            bucket = deepcopy(bucket)
        self._queue.put(bucket)

    def consume(self) -> Optional[List[Any]]:
        return self._queue.get()

    def get_current_size(self) -> int:
        return self._queue.qsize()

    def finish_producing(self, num_consumers: int):
        for _ in range(num_consumers):
            self._queue.put(NO_MORE_ITEMS)

    def close(self):
        pass


class InterProcessConnector(Connector):
    """Used for communication between Nodes at different processes pools."""

    def __init__(self, maxsize: Optional[int] = 0):
        super().__init__(maxsize=maxsize)

        if maxsize and maxsize > SemLock.SEM_VALUE_MAX:
            logger.warning(
                f"Limited maxsize for InterProcessConnector (Queue) since is bigger than OS limit: "
                f"{maxsize} > {SemLock.SEM_VALUE_MAX}"
            )
            self._maxsize = SemLock.SEM_VALUE_MAX

        self._queue: Optional[multiprocessing.Queue] = None

    def start(self):
        self._queue = multiprocessing.Queue(maxsize=self._maxsize)
        self._started = True

    def produce(self, bucket: List[Any]):
        self._queue.put(bucket)

    def consume(self) -> Optional[List[Any]]:
        bucket = self._queue.get()
        return bucket

    def get_current_size(self) -> int:
        return self._queue.qsize()

    def finish_producing(self, num_consumers: int):
        for _ in range(num_consumers):
            self._queue.put(NO_MORE_ITEMS)

    def close(self):
        self._queue.close()
