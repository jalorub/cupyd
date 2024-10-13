from multiprocessing import SimpleQueue, Value
from typing import List


# TODO: Not used, tentative to optimize the timings part
class TimingsBuffer:

    def __init__(self, maxsize: int = 25):
        super().__init__()
        self._maxsize = maxsize
        self._queue: SimpleQueue = SimpleQueue()
        self._buffer_size = Value("i", 0)

    def produce_timing(self, timing: float):
        with self._buffer_size.get_lock():
            if self._buffer_size.value >= self._maxsize:
                self._queue.get()  # make space in the buffer with the new timing
            else:
                self._buffer_size.value += 1
            self._queue.put(timing)

    def consume_buffer(self) -> List[float]:
        with self._buffer_size.get_lock():
            buffer_size = self._buffer_size.value
            if buffer_size == 0:
                timings = []
            else:
                timings = [self._queue.get() for _ in range(buffer_size)]
                self._buffer_size.value = 0

            return timings

    def close(self):
        self._queue.close()
