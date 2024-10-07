import logging
from collections import defaultdict
from copy import deepcopy
from multiprocessing import Queue, set_start_method, get_start_method
from time import time
from typing import List, Dict, Optional

from data_etl.core.communication.connector import (
    Connector,
    IntraProcessConnector,
    InterProcessConnector,
)
from data_etl.core.communication.counter import MPCounter
from data_etl.core.communication.event_flag import (
    InterProcessEventFlag,
    IntraProcessEventFlag,
)
from data_etl.core.communication.interruption_handler import InterruptionHandler
from data_etl.core.computing.etl_worker import ETLWorkerProcess, ETLWorkerThread
from data_etl.core.constants.logging import LOGGING_FORMAT
from data_etl.core.constants.sentinel_values import NO_MORE_ITEMS
from data_etl.core.exceptions import ETLExecutionError, InterruptedETL
from data_etl.core.graph.algorithms import (
    get_etl_segments,
    topological_sort,
    assign_names_and_ids_to_nodes,
)
from data_etl.core.graph.classes import Node
from data_etl.core.models.etl_segment import ETLSegment
from data_etl.core.models.node_exception import NodeException
from data_etl.core.nodes import Loader
from data_etl.core.nodes.extractor import Extractor
from data_etl.core.stats.progress_thread import ProgressThread
from data_etl.core.stats.timings_thread import TimingsThread
from data_etl.core.utils import format_seconds, get_subdict

logger = logging.getLogger("data_etl.etl")


class ETL:

    def __init__(self, extractor: Extractor):
        if not isinstance(extractor, Extractor):
            raise TypeError(f"Invalid Extractor: {type(extractor)}")
        self.extractor = extractor

    def run(
        self,
        workers: int = 1,
        raise_exception: bool = True,
        raise_exception_if_interrupted: bool = True,
        monitor_performance: bool = False,
        show_progress: bool = True,
        verbose: bool = True,
    ):
        start_method = get_start_method()
        set_start_method("spawn", force=True)  # ETLWorkerProcesses will be spawned

        current_formatter, current_level, current_logfile = self._setup_logger()

        (
            nodes,
            segments_by_id,
            stop_event,
            pause_event,
            interruption_handler,
            node_timings,
            finished_workers,
            monitor_performance_event_by_node_id,
            counter_by_node_id,
        ) = self._build(num_workers=workers, monitor_performance=monitor_performance)

        if verbose:
            logger.info("ETL build successful, running ETL...")

        start_time = time()
        exceptions_by_node_id: Dict[str, List[NodeException]] = defaultdict(list)

        # this will handle interruptions in this main process (and the ETLWorkerThreads)
        interruption_handler.start()

        if monitor_performance:
            timings_thread = TimingsThread(
                nodes=nodes, node_timings=node_timings, stop_event=stop_event
            )
            timings_thread.start()
        else:
            timings_thread = None

        if show_progress:
            finalize_event = IntraProcessEventFlag()
            progress_thread = ProgressThread(
                nodes=nodes,
                counter_by_node_id=counter_by_node_id,
                stop_event=stop_event,
                finalize_event=finalize_event,
            )
            progress_thread.start()
        else:
            progress_thread, finalize_event = None, None

        # start all ETLWorkers
        for segment in segments_by_id.values():
            for worker in segment.workers_by_id.values():
                worker.start()

        # auxiliary structures to easily access segment resources
        active_worker_ids_by_segment_id = {}
        workers_by_id = {}

        for segment_id, segment in segments_by_id.items():
            active_worker_ids_by_segment_id[segment_id] = set(
                segment.workers_by_id.keys()
            )

            for worker_id, worker in segment.workers_by_id.items():
                workers_by_id[worker_id] = worker

        logger.info(f"ETL startup time: {round(time() - start_time, 4)} seconds")

        # run until all ETLSegments are finished
        while active_worker_ids_by_segment_id:
            try:
                worker_id, segment_id, exception_by_node_id = finished_workers.get()
                workers_by_id[worker_id].join()
                active_worker_ids_by_segment_id[segment_id].remove(worker_id)

                if exception_by_node_id:
                    for node_id, exception in exception_by_node_id.items():
                        exceptions_by_node_id[node_id].append(exception)

                # if whole segment has finished, we will trigger the finalization of other connected
                # nodes (from other segments if connected via InterProcessConnector)
                if not active_worker_ids_by_segment_id[segment_id]:
                    active_worker_ids_by_segment_id.pop(segment_id)

                    for output_segment_num_workers, connector in segments_by_id[
                        segment_id
                    ].output_interprocess_connectors:
                        for _ in range(output_segment_num_workers):
                            connector.produce(NO_MORE_ITEMS)
            except InterruptedError:
                continue

        # stop the TimingsThread & ProgressThread, if running
        if monitor_performance:
            node_timings.put(NO_MORE_ITEMS)
            timings_thread.join()

        if show_progress:
            finalize_event.set()
            progress_thread.join()

        # close InterProcessConnectors
        for segment in segments_by_id.values():
            for _, connector in segment.output_interprocess_connectors:
                connector.close()

        elapsed_time = format_seconds(time() - start_time)

        set_start_method(start_method, force=True)  # restore start method

        if exceptions_by_node_id:
            failed_nodes_names = []
            for node in nodes:
                if node.id in exceptions_by_node_id:
                    failed_nodes_names.append(node.name)
            failed_nodes_names.sort()
            logger.error(
                f'ETL finished with errors in nodes: {", ".join(failed_nodes_names)} | '
                f"Elapsed time: {elapsed_time}"
            )
        else:
            if interruption_handler.interrupted():
                if raise_exception_if_interrupted:
                    raise InterruptedETL(f"Elapsed time: {elapsed_time}")
                else:
                    logger.warning(f"ETL interrupted! | {elapsed_time}")
            else:
                logger.info(f"ETL finished | Elapsed time: {elapsed_time}")

        self._reset_root_logging(
            current_level=current_level,
            current_formatter=current_formatter,
            current_logfile=current_logfile,
        )

        if exceptions_by_node_id and raise_exception:
            # we will only raise one exception although maybe multiple occurred
            for exceptions in exceptions_by_node_id.values():
                raise ETLExecutionError(exceptions[0].traceback_formatted)

    def _build(self, num_workers: int, monitor_performance: bool):
        """Build the ETL."""

        # 1. List all nodes & edges & ensure the ETL is a DAG
        nodes, edges = topological_sort(root_node=self.extractor)

        # 2. Each node will have its unique ID + an autogenerated name (if any wasn't provided)
        assign_names_and_ids_to_nodes(nodes=nodes)

        # 3. Determine the ETLSegments of the ETL. Each ETLSegment will consist in a group of
        # consecutive nodes that will run on the same ETLWorker
        segments = get_etl_segments(nodes=nodes, num_workers=num_workers)

        # 4. Create the ETL connectors
        input_connector_by_node_id: Dict[str, Connector] = {}
        output_connectors_by_node_id: Dict[str, List[Connector]] = defaultdict(list)

        for edge in edges:
            origin: Node = edge.origin
            target: Node = edge.target

            origin_segment = None
            target_segment = None

            for segment in segments:
                if origin.id in segment.node_ids:
                    origin_segment = segment
                if target.id in segment.node_ids:
                    target_segment = segment

            # TODO: allow customizing these max sizes when configuring the ETL/Nodes
            if origin_segment.id == target_segment.id:
                connector = IntraProcessConnector(maxsize=0)
            else:
                connector = InterProcessConnector(maxsize=0)
                connector.start()

            input_connector_by_node_id[target.id] = connector
            output_connectors_by_node_id[origin.id].append(connector)

            if isinstance(connector, InterProcessConnector):
                origin_segment.output_interprocess_connectors.append(
                    (target_segment.num_workers, connector)
                )

        # 5. Create necessary structures & ETL Workers
        worker_num = 1
        finished_workers = Queue()
        node_timings = Queue(maxsize=100_000)  # todo: might cause slowdowns, rethink?
        stop_event = InterProcessEventFlag()
        pause_event = InterProcessEventFlag()
        interruption_handler = InterruptionHandler(stop_event=stop_event)
        counter_by_node_id: Dict[str, MPCounter] = {
            node.id: MPCounter()
            for node in nodes
            if isinstance(node, Loader) and not node.outputs
        }
        monitor_performance_event_by_node_id = {
            node.id: InterProcessEventFlag(start_set=monitor_performance)
            for node in nodes
        }
        segments_by_id: Dict[str, ETLSegment] = {}

        for segment in segments:
            worker_class = (
                ETLWorkerThread if segment.run_in_main_process else ETLWorkerProcess
            )

            for _ in range(segment.num_workers):
                etl_worker_id = f"etl_worker_{worker_num}"

                etl_worker = worker_class(
                    worker_id=etl_worker_id,
                    segment_id=segment.id,
                    nodes=segment.nodes,
                    counters=get_subdict(
                        dictionary=counter_by_node_id, keys=segment.node_ids
                    ),
                    input_connector_by_node_id=get_subdict(
                        dictionary=input_connector_by_node_id, keys=segment.node_ids
                    ),
                    output_connectors_by_node_id=get_subdict(
                        dictionary=output_connectors_by_node_id, keys=segment.node_ids
                    ),
                    monitor_performance_event_by_node_id=get_subdict(
                        dictionary=monitor_performance_event_by_node_id,
                        keys=segment.node_ids,
                    ),
                    stop_event=stop_event,
                    pause_event=pause_event,
                    interruption_handler=interruption_handler,
                    node_timings=node_timings,
                    finished_workers=finished_workers,
                )
                segment.workers_by_id[etl_worker_id] = etl_worker
                worker_num += 1

            segments_by_id[segment.id] = segment

        return (
            nodes,
            segments_by_id,
            stop_event,
            pause_event,
            interruption_handler,
            node_timings,
            finished_workers,
            monitor_performance_event_by_node_id,
            counter_by_node_id,
        )

    @staticmethod
    def _setup_logger() -> [logging.Formatter, int, Optional[str]]:
        """Update the current logger handler & backup the current logging configuration."""

        try:
            current_formatter = deepcopy(logging.root.handlers[0].formatter)
        except TypeError:
            logger.warning("Unable to get current logger")
            return None, None, None

        current_level = logging.root.level

        try:
            current_logfile = logging.root.handlers[0].baseFilename
        except AttributeError:
            current_logfile = None

        if current_logfile:
            logger_handler = logging.FileHandler(filename=current_logfile)
        else:
            logger_handler = logging.StreamHandler()

        logger_handler.setLevel(logging.INFO)
        logger_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
        logger.propagate = False
        logger.addHandler(logger_handler)

        return current_formatter, current_level, current_logfile

    @staticmethod
    def _reset_root_logging(
        current_level: Optional[int],
        current_formatter: Optional[logging.Formatter],
        current_logfile: Optional[str],
    ):
        """Restore the old logging configuration."""

        if not current_formatter:
            return None

        logging.root.setLevel(current_level)
        for idx, h in enumerate(logging.root.handlers):
            if current_logfile:
                handler = logging.FileHandler(filename=current_logfile)
                handler.setFormatter(current_formatter)
                logging.root.handlers[idx] = handler
            else:
                h.setFormatter(current_formatter)
