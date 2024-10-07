from dataclasses import dataclass, field
from typing import List, Set, Union, Dict, Tuple

from data_etl.core.communication import InterProcessConnector
from data_etl.core.computing.etl_worker import ETLWorkerThread, ETLWorkerProcess
from data_etl.core.graph.classes import Node


@dataclass
class ETLSegment:
    id: str
    nodes: List[Node]
    node_ids: Set[str]
    run_in_main_process: bool
    num_workers: int

    # these will be filled when building the ETL
    workers_by_id: Dict[str, Union[ETLWorkerThread, ETLWorkerProcess]] = field(
        default_factory=lambda: dict()
    )
    # first tuple element is the amount of ETLWorkers that are consuming from the Connector
    output_interprocess_connectors: List[Tuple[int, InterProcessConnector]] = field(
        default_factory=lambda: []
    )
