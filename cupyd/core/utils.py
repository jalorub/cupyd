from datetime import timedelta
from typing import Union, Dict, Iterable


def format_seconds(seconds: Union[int, float]) -> str:
    return str(timedelta(seconds=seconds))


def get_subdict(dictionary: Dict, keys: Iterable[str]) -> Dict:
    return {key: dictionary[key] for key in keys if key in dictionary}
