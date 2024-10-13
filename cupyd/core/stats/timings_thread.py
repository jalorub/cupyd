import logging
from collections import deque
from itertools import chain
from multiprocessing import Queue
from statistics import median
from threading import Thread
from time import time
from typing import Optional, List, Dict

from cupyd.core.communication import InterProcessEventFlag
from cupyd.core.constants.logging import LOGGING_MSG_PADDING
from cupyd.core.constants.sentinel_values import NO_MORE_ITEMS
from cupyd.core.graph.classes import Node

logger = logging.getLogger("cupyd.timings")


class TimingsThread(Thread):

    def __init__(
        self,
        nodes: List[Node],
        node_timings: Queue,
        stop_event: InterProcessEventFlag,
        refresh_interval: int = 5,  # seconds
    ):
        super().__init__(name="cupyd")
        self.node_timings = node_timings
        self.stop_event = stop_event
        self.refresh_interval = refresh_interval
        self.node_name_by_id = {node.id: node.name for node in nodes}
        self.stats_by_node_id: Dict[str, Dict[str, Optional[float]]] = {
            node.id: {"min": None, "max": None, "median": None} for node in nodes
        }
        self.buffer_by_node_id: Dict[str, deque[float]] = {
            node.id: deque(maxlen=100) for node in nodes
        }

    def run(self):
        last_log_time = time()

        while True:
            item = self.node_timings.get()

            if item is NO_MORE_ITEMS:
                break
            elif self.stop_event:
                continue
            else:
                node_id, timing = item

            self.buffer_by_node_id[node_id].append(timing)

            current_time = time()

            if (last_log_time - current_time) >= self.refresh_interval:
                last_log_time = current_time
                self._update_timings()
                self._log_timings()

        if not self.stop_event:
            self._update_timings()
            self._log_timings()

    def _update_timings(self):
        for node_id, timings in self.buffer_by_node_id.items():
            if timings:
                current_min: List[float] = []
                current_max: List[float] = []

                if self.stats_by_node_id[node_id]["min"]:
                    current_min = [self.stats_by_node_id[node_id]["min"]]
                    current_max = [self.stats_by_node_id[node_id]["max"]]

                self.stats_by_node_id[node_id]["min"] = min(chain(timings, current_min))
                self.stats_by_node_id[node_id]["max"] = max(chain(timings, current_max))
                self.stats_by_node_id[node_id]["median"] = median(timings)

    def _log_timings(self):
        log = "timings:\n"
        for node_id, stats in self.stats_by_node_id.items():
            min_timing = self._format_timing(stats["min"])
            max_timing = self._format_timing(stats["max"])
            median_timing = self._format_timing(stats["median"])

            log += (
                f"{LOGGING_MSG_PADDING}\t• {self.node_name_by_id[node_id]}\n"
                f"{LOGGING_MSG_PADDING}\t\t"
                f"{median_timing} (avg) | {min_timing} (min) | {max_timing} (max)\n"
            )

        logger.info(log)

    @staticmethod
    def _format_timing(value: Optional[float]) -> str:
        if value is None:
            return "no_measure"

        if 1 <= value < 60:
            return f"{round(value, 2)} s"
        elif value < 1:
            ms_value = value * 1000
            if ms_value < 1:
                return f"{round(ms_value * 1000, 4)} μs"
            else:
                return f"{round(ms_value, 4)} ms"
        else:
            minutes_value = value / 60
            if minutes_value <= 1:
                return f"{round(minutes_value, 2)} min"
            else:
                return f"{round(minutes_value / 60, 4)} hours"
