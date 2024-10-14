from __future__ import annotations

from abc import abstractmethod
from re import compile as re_compile
from typing import List, Union, Tuple, Iterable, Any, final, Optional

from cupyd.core.exceptions import (
    CyclicNodeError,
    NodesAlreadyConnectedError,
    NodesConnectionError,
)
from cupyd.core.models.node_exception import NodeException

__all__ = ["Node", "Edge", "SubGraph"]

NODE_NAME_REGEX = re_compile(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+")


class _Connectable:

    @abstractmethod
    def __rshift__(self, target: Union[_Connectable, List[_Connectable]]):
        raise NotImplementedError


class Node(_Connectable):

    def __init__(self):
        self._id: Optional[str] = None
        self._name: Optional[str] = None
        self._input: Optional[Node] = None
        self._outputs: List[Node] = []

    @final
    def __str__(self) -> str:
        if self._name:
            return self._name
        else:
            # build a snake_case representation out of the CamelCase class name
            class_name = self.__class__.__name__
            tokens = [str(token).lower() for token in NODE_NAME_REGEX.findall(class_name)]
            return "_".join(tokens)

    @final
    def __repr__(self) -> str:
        return str(self)

    @final
    def __rshift__(self, target: Union[_Connectable, List[_Connectable]]) -> SubGraph:
        return _NodeConnector.connect(origin=self, target=target)

    def start(self):
        """Code to run on Node initialization."""
        pass

    def finalize(self):
        """Code to run on Node finalization."""
        pass

    def handle_exception(self, exception: NodeException):
        """Code to run on Node exception.

        By default, the finalize() method will be called, no matter the exception.
        The user may override it to add custom behaviour based on the raised Exception,
        but should remember to call finalize(), if necessary.

        Parameters
        ----------
        exception : NodeException
            Exception that occurred inside the Node.

        Returns
        -------
        None
        """

        self.finalize()

    @property
    def input(self) -> Optional[Node]:
        return self._input

    @input.setter
    def input(self, node: Node):
        if not isinstance(node, Node):
            raise TypeError(f"Unable to set input node with {node}")
        if self._input:
            raise NodesConnectionError(
                "Node input was already set. Please, for safety, create a new Node instance "
                "instead of re-using an old one"
            )
        if node == self:
            raise CyclicNodeError("Unable to connect Node with itself!")
        self._input = node

    @property
    def outputs(self) -> List[Node]:
        return self._outputs

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError
        self._name = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value: str):
        if not isinstance(value, str):
            raise TypeError
        self._id = value


class Edge:

    def __init__(self, origin: Node, target: Node):
        self.origin = origin
        self.target = target

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Edge):
            return (self.origin == other.origin) and (self.target == other.target)
        else:
            raise TypeError(f"Comparison error between edge and {type(other)}")

    def __str__(self) -> str:
        return f"{self.origin} ⇒ {self.target}"

    def __repr__(self) -> str:
        return str(self)

    def to_tuple(self) -> Tuple[Node, Node]:
        return self.origin, self.target

    def to_str_tuple(self) -> Tuple[str, str]:
        return str(self.origin), str(self.target)


class SubGraph(_Connectable):
    """A subset of Nodes within a Directed Acyclic Graph (DAG)."""

    def __init__(self, root_node: Node, leaf_nodes: Iterable[Node] = None):
        if not root_node:
            raise ValueError("Cannot initialize a SubGraph without a root Node!")

        self.root_node = root_node
        self.leaf_nodes = tuple(node for node in leaf_nodes) if leaf_nodes else ()

    def __rshift__(self, target: Union[_Connectable, List[_Connectable]]) -> SubGraph:
        origin = self.leaf_nodes or self.root_node

        if isinstance(origin, tuple):
            if len(origin) > 1:
                raise NodesConnectionError(
                    f"Forbidden to connect multiple Nodes {origin} into another {target}"
                )
            else:
                origin = origin[0]

        subgraph = _NodeConnector.connect(origin=origin, target=target)

        return SubGraph(root_node=self.root_node, leaf_nodes=subgraph.leaf_nodes)


class _NodeConnector:

    @classmethod
    def connect(cls, origin: Node, target: Union[_Connectable, List[_Connectable]]) -> SubGraph:
        """Connect a list of Nodes to one of the following Connectable:

        a) Another Node.
        b) A SubGraph
        c) A list of Nodes and/or SubGraphs.

        Lastly, return the resulting SubGraph.
        """

        target_root_nodes, target_leaf_nodes = cls._get_nodes_from_target(target)

        for target_node in target_root_nodes:
            cls._connect_nodes(origin=origin, target=target_node)

        subgraph = SubGraph(root_node=origin, leaf_nodes=target_leaf_nodes)

        return subgraph

    @staticmethod
    def _get_nodes_from_target(
        target: Union[_Connectable, List[_Connectable]]
    ) -> Tuple[List[Node], List[Node]]:

        target_root_nodes = []
        target_leaf_nodes = []

        if isinstance(target, Iterable):
            for d in target:
                if isinstance(d, Node):
                    target_root_nodes.append(d)
                    target_leaf_nodes.append(d)
                elif isinstance(d, SubGraph):
                    target_root_nodes.append(d.root_node)
                    if d.leaf_nodes:
                        target_leaf_nodes.extend(d.leaf_nodes)
                    else:
                        target_leaf_nodes.append(d.root_node)
                else:
                    raise TypeError(f"Cannot connect to a {type(target)} target object.")
        elif isinstance(target, Node):
            target_root_nodes = [target]
            target_leaf_nodes = [target]
        elif isinstance(target, SubGraph):
            target_root_nodes = [target.root_node]
            target_leaf_nodes = list(target.leaf_nodes) or [target.root_node]
        else:
            raise TypeError(f"Cannot connect to a {type(target)} target object.")

        return target_root_nodes, target_leaf_nodes

    @staticmethod
    def _connect_nodes(origin: Node, target: Node):
        """Connect two Nodes.

        Two checks must pass before making the connection:

            1. We are not connecting the Node with itself.
            2. Both Nodes are not already connected.
        """

        if origin == target:
            raise CyclicNodeError(f"Cannot connect a Node with itself: {origin}")

        if any(node == target for node in origin.outputs):
            raise NodesAlreadyConnectedError(f"Node {origin} already connected to {target}")

        target.input = origin
        origin.outputs.append(target)
