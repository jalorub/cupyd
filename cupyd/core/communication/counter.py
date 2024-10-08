from multiprocessing import RawValue, Lock


class MPCounter:
    def __init__(self):
        self._value = RawValue("i", 0)
        self._lock = Lock()

    def increase(self, amount: int):
        with self._lock:
            self._value.value += amount

    @property
    def value(self):
        return self._value.value
