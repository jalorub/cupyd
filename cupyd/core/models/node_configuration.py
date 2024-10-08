from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractorConfiguration:
    bucket_size: int = 1000
    run_in_main_process: bool = True


@dataclass
class TransformerConfiguration:
    input_key: str = None
    run_in_main_process: bool = False


@dataclass
class FilterConfiguration:
    input_key: str = None
    value_to_filter: Any = None
    disable_safe_copy: bool = False
    run_in_main_process: bool = False


@dataclass
class LoaderConfiguration:
    input_key: str = None
    disable_safe_copy: bool = False
    run_in_main_process: bool = False


@dataclass
class BulkerConfiguration:
    run_in_main_process: bool = False


class DeBulkerConfiguration:
    run_in_main_process: bool = False
