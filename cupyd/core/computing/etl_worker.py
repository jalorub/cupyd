import logging
from multiprocessing import Process
from multiprocessing import Queue as MultiprocessingQueue
from queue import Queue
from threading import Thread
from typing import List, Dict, Type, Tuple

from cupyd.core.communication import (
    Connector,
    InterProcessEventFlag,
    IntraProcessConnector,
    MPCounter,
    InterruptionHandler,
)
from cupyd.core.computing.node_worker import (
    NodeWorker,
    ExtractorWorker,
    ProcessorWorker,
    DeBulkerWorker,
    BulkerWorker,
)
from cupyd.core.constants.logging import LOGGING_FORMAT
from cupyd.core.constants.sentinel_values import NO_MORE_ITEMS
from cupyd.core.graph.classes import Node
from cupyd.core.models.node_exception import NodeException
from cupyd.core.nodes import Extractor, Transformer, Loader, Filter, Bulker, DeBulker


class ETLWorker:

    def __init__(
        self,
        worker_id: str,
        segment_id: str,
        nodes: List[Node],
        counters: Dict[str, MPCounter],
        input_connector_by_node_id: Dict[str, Connector],
        output_connectors_by_node_id: Dict[str, List[Connector]],
        monitor_performance_event_by_node_id: Dict[str, InterProcessEventFlag],
        stop_event: InterProcessEventFlag,
        pause_event: InterProcessEventFlag,
        interruption_handler: InterruptionHandler,
        node_timings: MultiprocessingQueue,
        finished_workers: MultiprocessingQueue,
    ):
        super().__init__()
        self.worker_id = worker_id
        self.segment_id = segment_id
        self.nodes = nodes
        self.counters = counters
        self.input_connector_by_node_id = input_connector_by_node_id
        self.output_connectors_by_node_id = output_connectors_by_node_id
        self.monitor_performance_event_by_node_id = monitor_performance_event_by_node_id
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.node_timings = node_timings
        self.interruption_handler = interruption_handler
        self.finished_workers = finished_workers

    def run(self):
        logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, force=True)

        if isinstance(self, ETLWorkerProcess):
            self.interruption_handler.start()

        thread_by_node_id: Dict[str, NodeWorker] = {}
        finished_threads_queue: Queue[Tuple[str, NodeException]] = Queue()

        # start IntraProcessConnectors (InterProcessConnectors were started outside the ETLWorker)
        for connector in self.input_connector_by_node_id.values():
            if isinstance(connector, IntraProcessConnector):
                connector.start()

        # each Node will have its own thread
        for node in self.nodes:
            thread_class = self._get_node_worker_class(node=node)
            thread = thread_class(
                node=node,
                counter=self.counters.get(node.id, None),
                input_connector=self.input_connector_by_node_id.get(node.id, None),
                output_connectors=self.output_connectors_by_node_id.get(node.id, []),
                finished_threads_queue=finished_threads_queue,
                stop_event=self.stop_event,
                pause_event=self.pause_event,
                node_timings=self.node_timings,
                monitor_performance=self.monitor_performance_event_by_node_id[node.id],
            )
            thread.start()
            thread_by_node_id[node.id] = thread

        exception_by_node_id: Dict[str, NodeException] = {}

        while thread_by_node_id:
            node_id, exception = finished_threads_queue.get()

            # safely wait till the thread is completely finished
            thread_by_node_id.pop(node_id).join()

            # send sentinel value to every IntraProcessConnector that is output of the finished
            # Node, if any. InterProcessConnectors will be handled from the main process thread
            for connector in self.output_connectors_by_node_id.get(node_id, []):
                if isinstance(connector, IntraProcessConnector):
                    connector.produce(NO_MORE_ITEMS)

            if exception:
                exception_by_node_id[node_id] = exception

        # notify the main process thread this ETLWorker has finished
        self.finished_workers.put((self.worker_id, self.segment_id, exception_by_node_id))

    @staticmethod
    def _get_node_worker_class(node: Node) -> Type[NodeWorker]:
        if isinstance(node, Extractor):
            return ExtractorWorker
        elif isinstance(node, Transformer) or isinstance(node, Filter) or isinstance(node, Loader):
            return ProcessorWorker
        elif isinstance(node, Bulker):
            return BulkerWorker
        elif isinstance(node, DeBulker):
            return DeBulkerWorker
        else:
            raise TypeError(f"Invalid node type: {type(node)}")


class ETLWorkerThread(ETLWorker, Thread):
    pass


class ETLWorkerProcess(ETLWorker, Process):
    pass
