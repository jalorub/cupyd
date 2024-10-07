from __future__ import annotations

from abc import abstractmethod
from typing import Any, final

from data_etl.core.graph.classes import Node
from data_etl.core.models.node_configuration import FilterConfiguration


class Filter(Node):
    def __init__(self):
        super().__init__()
        self._configuration = FilterConfiguration()

    @abstractmethod
    def filter(self, item: Any) -> Any:
        """Filter an incoming item (Python object)."""

        raise NotImplementedError('Missing implementation of filter() method!')

    @final
    @property
    def configuration(self):
        return self._configuration
