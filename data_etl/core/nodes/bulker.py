from __future__ import annotations

from typing import final

from data_etl.core.graph.classes import Node
from data_etl.core.models.node_configuration import BulkerConfiguration


class Bulker(Node):
    def __init__(self, bulk_size: int = 1000):
        super().__init__()
        self.bulk_size = bulk_size
        self._configuration = BulkerConfiguration()

    @final
    @property
    def configuration(self):
        return self._configuration
