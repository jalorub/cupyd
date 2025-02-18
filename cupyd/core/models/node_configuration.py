from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_QUEUE_MAX_SIZE = 10_000


@dataclass
class ExtractorConfiguration:
    bucket_size: int = 1000
    run_in_main_process: bool = True


@dataclass
class TransformerConfiguration:
    input_key: str = None
    run_in_main_process: bool = False
    queue_max_size: Optional[int] = DEFAULT_QUEUE_MAX_SIZE


@dataclass
class FilterConfiguration:
    input_key: str = None
    value_to_filter: Any = None
    disable_safe_copy: bool = False
    run_in_main_process: bool = False
    queue_max_size: Optional[int] = DEFAULT_QUEUE_MAX_SIZE


@dataclass
class LoaderConfiguration:
    input_key: str = None
    disable_safe_copy: bool = False
    run_in_main_process: bool = False
    queue_max_size: Optional[int] = DEFAULT_QUEUE_MAX_SIZE


@dataclass
class BulkerConfiguration:
    run_in_main_process: bool = False
    queue_max_size: Optional[int] = DEFAULT_QUEUE_MAX_SIZE


class DeBulkerConfiguration:
    run_in_main_process: bool = False
    queue_max_size: Optional[int] = DEFAULT_QUEUE_MAX_SIZE
