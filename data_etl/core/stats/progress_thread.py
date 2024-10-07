import logging
from threading import Thread
from time import sleep
from typing import List, Dict

from data_etl.core.communication.counter import MPCounter
from data_etl.core.communication.event_flag import (
    IntraProcessEventFlag,
    InterProcessEventFlag,
)
from data_etl.core.constants.logging import LOGGING_MSG_PADDING
from data_etl.core.graph.classes import Node

logger = logging.getLogger("data_etl.progress")


class ProgressThread(Thread):

    def __init__(
        self,
        nodes: List[Node],
        counter_by_node_id: Dict[str, MPCounter],
        finalize_event: IntraProcessEventFlag,
        stop_event: InterProcessEventFlag,
        refresh_interval: float = 2.5,  # seconds
    ):
        super().__init__(name="data_etl (progress)")
        self.finalize_event = finalize_event
        self.stop_event = stop_event
        self.refresh_interval = refresh_interval
        self.counter_by_node_name = {}

        for node in nodes:
            if node.id in counter_by_node_id:
                self.counter_by_node_name[node.name] = counter_by_node_id[node.id]

    def run(self):
        last_state = self._get_counters_state()

        while not self.finalize_event and not self.stop_event:
            new_state = self._get_counters_state()
            if new_state != last_state:
                last_state = new_state
                self._log_progress()
            sleep(self.refresh_interval)

        if not self.stop_event:
            self._log_progress(last_log=True)

    def _get_counters_state(self):
        return {
            node_name: int(counter.value)
            for node_name, counter in self.counter_by_node_name.items()
        }

    def _log_progress(self, last_log: bool = False):
        if last_log:
            log = "[FINISHED] progress:\n"
        else:
            log = "progress:\n"

        for node_name, counter in self.counter_by_node_name.items():
            total_items = f"{counter.value:,}"
            log += f"{LOGGING_MSG_PADDING}\t• {node_name}: {total_items}\n"
        logger.info(log)
