from __future__ import annotations

from abc import abstractmethod
from typing import Any, Iterator, final

from cupyd.core.graph.classes import Node
from cupyd.core.models.node_configuration import ExtractorConfiguration


class Extractor(Node):
    def __init__(self):
        super().__init__()
        self._configuration = ExtractorConfiguration()

    @abstractmethod
    def extract(self) -> Iterator[Any]:
        """Extract an item."""

        raise NotImplementedError("Missing implementation of extract() method!")

    @final
    @property
    def configuration(self):
        return self._configuration
