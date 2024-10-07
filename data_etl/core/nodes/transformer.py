from __future__ import annotations

from abc import abstractmethod
from typing import Any, final

from data_etl.core.graph.classes import Node
from data_etl.core.models.node_configuration import TransformerConfiguration


class Transformer(Node):
    def __init__(self):
        super().__init__()
        self._configuration = TransformerConfiguration()

    @abstractmethod
    def transform(self, item: Any) -> Any:
        """Transform an incoming item (Python object)."""

        raise NotImplementedError('Missing implementation of transform() method!')

    @final
    @property
    def configuration(self):
        return self._configuration
