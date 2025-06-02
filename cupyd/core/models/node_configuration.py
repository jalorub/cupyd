from dataclasses import dataclass
from typing import Any, Optional

# max number of items that can be stored in a bucket
DEFAULT_BUCKET_SIZE = 100

# max number of buckets that can be stored in a queue
DEFAULT_QUEUE_MAX_SIZE = 500


@dataclass
class ExtractorConfiguration:
    bucket_size: int = DEFAULT_BUCKET_SIZE
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
