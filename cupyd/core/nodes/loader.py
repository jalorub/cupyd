from __future__ import annotations

from abc import abstractmethod
from typing import Any, final

from cupyd.core.graph.classes import Node
from cupyd.core.models.node_configuration import LoaderConfiguration


class Loader(Node):
    def __init__(self):
        super().__init__()
        self._configuration = LoaderConfiguration()

    @abstractmethod
    def load(self, item: Any):
        """Load an incoming item (Python object)."""

        raise NotImplementedError("Missing implementation of load() method!")

    @final
    @property
    def configuration(self):
        return self._configuration
