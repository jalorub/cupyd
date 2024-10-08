from __future__ import annotations

from typing import final

from cupyd.core.graph.classes import Node
from cupyd.core.models.node_configuration import DeBulkerConfiguration


class DeBulker(Node):
    def __init__(self):
        super().__init__()
        self._configuration = DeBulkerConfiguration()

    @final
    @property
    def configuration(self):
        return self._configuration
