import typing
from collections import defaultdict
from itertools import groupby
from typing import List, Tuple

from cupyd.core.graph.classes import Node, Edge
from cupyd.core.models.etl_segment import ETLSegment
from cupyd.core.nodes import Extractor, Transformer, Loader, Filter, Bulker, DeBulker


# PUBLIC FUNCTIONS


def topological_sort(root_node: Node) -> Tuple[List[Node], List[Edge]]:
    nodes: List[Node] = []
    edges: List[Edge] = []

    # if the graph contains cycles (not a DAG), it will fail when computing the topological sort.
    nodes, edges = _downstream_discovery(root_node, nodes, edges)

    return nodes, edges


def assign_names_and_ids_to_nodes(nodes: List[Node]) -> None:
    """If a Node doesn't have a name provide it one using the class name with a numbered suffix."""

    node_id = 1
    num_nodes_per_class: defaultdict[str, int] = defaultdict(int)
    last_num_per_class: defaultdict[str, int] = defaultdict(int)

    for node in nodes:
        node.id = f"node_{node_id}"
        node_id += 1

        if node.name is None:
            class_name = str(node)
            num_nodes_per_class[class_name] += 1

    for node in nodes:
        if node.name is None:
            class_name = str(node)
            last_num_per_class[class_name] += 1
            if num_nodes_per_class[class_name] == 1:  # single Node from that class without name
                node.name = class_name
            else:
                node.name = f"{class_name}_{last_num_per_class[class_name]}"


def get_etl_segments(nodes: List[Node], num_workers: int) -> List[ETLSegment]:
    segments = []
    segment_num = 1

    for group in _split_nodes_by_attr(nodes=nodes, attr_name="run_in_main_process"):
        for group_ in _split_nodes_if_not_consecutive(nodes=group):
            run_in_main_process = group_[0].configuration.run_in_main_process  # type: ignore

            if run_in_main_process or isinstance(group_[0], Extractor):
                segment_num_workers = 1
            else:
                segment_num_workers = num_workers

            segments.append(
                ETLSegment(
                    id=f"segment_{segment_num}",
                    nodes=group_,
                    node_ids={node.id for node in group_},
                    num_workers=segment_num_workers,
                    run_in_main_process=run_in_main_process,
                )
            )
            segment_num += 1

    return segments


# PROTECTED FUNCTIONS


def _downstream_discovery(
    node: Node, nodes: List[Node], edges: List[Edge]
) -> Tuple[List[Node], List[Edge]]:
    """Discover unique Nodes and Edges from top to bottom, from left to right."""

    if not nodes:
        nodes = []
    if not edges:
        edges = []

    if node not in nodes:  # avoid storing duplicate Nodes when at least 2 branches are connected
        nodes.append(node)

    for descendant in node.outputs:
        edge = Edge(origin=node, target=descendant)

        if edge not in edges:
            edges.append(edge)

        nodes, edges = _downstream_discovery(descendant, nodes, edges)

    return nodes, edges


def _split_nodes_by_attr(nodes: List[Node], attr_name: str) -> List[List[Node]]:
    """This function will split Nodes based on equality of a selected Node attribute."""

    groups = [
        list(g)
        for _, g in groupby(
            sorted(nodes, key=lambda x: _get_node_attr(x, attr_name)),
            key=lambda x: _get_node_attr(x, attr_name),
        )
    ]
    return groups


def _get_ascendants(
    node: Node, ascendants: List[Node] = None, valid_nodes_ids: typing.Set[str] = None
) -> List[Node]:
    if not ascendants:
        ascendants = []

    if node.input:
        if (valid_nodes_ids and node.input.id in valid_nodes_ids) or not valid_nodes_ids:
            ascendants.append(node.input)
            ascendants.extend(_get_ascendants(node=node.input, ascendants=ascendants))

    return ascendants


def _get_descendants(
    node: Node, descendants: List[Node] = None, valid_nodes_ids: typing.Set[str] = None
) -> List[Node]:
    if not descendants:
        descendants = []

    for output_node in node.outputs:
        if (valid_nodes_ids and output_node.id in valid_nodes_ids) or not valid_nodes_ids:
            descendants.append(output_node)
            descendants.extend(_get_descendants(node=output_node, descendants=descendants))

    return descendants


def _split_nodes_if_not_consecutive(nodes: List[Node]) -> List[List[Node]]:
    node_ids_to_check = {node.id for node in nodes}
    connected_nodes_by_id = {}

    for node in nodes:
        connected_nodes_by_id[node.id] = {node.id}

        for ascendant in _get_ascendants(node=node, valid_nodes_ids=node_ids_to_check):
            if ascendant.id in node_ids_to_check:
                connected_nodes_by_id[node.id].add(ascendant.id)

        for descendant in _get_descendants(node=node, valid_nodes_ids=node_ids_to_check):
            if descendant.id in node_ids_to_check:
                connected_nodes_by_id[node.id].add(descendant.id)

    groups = []

    while connected_nodes_by_id:
        node_id, connected_nodes = connected_nodes_by_id.popitem()
        node_ids_group = {node_id}

        for node_id_, connected_nodes_ in connected_nodes_by_id.items():

            # path exists between both nodes
            if connected_nodes.intersection(connected_nodes_):
                node_ids_group.add(node_id_)

        for node_id in node_ids_group:
            connected_nodes_by_id.pop(node_id, None)

        group = []

        for node in nodes:
            if node.id in node_ids_group:
                group.append(node)

        groups.append(group)

    # extractor nodes must be alone if they don't have run_in_main_process
    for group in groups:
        num_nodes = len(group)
        if num_nodes > 1:
            for idx in range(num_nodes):
                node = group[idx]
                if isinstance(node, Extractor) and not node.configuration.run_in_main_process:
                    group.pop(idx)
                    groups.append([node])
                    return groups

    return groups


def _get_node_attr(
    node: typing.Union[Node, Extractor, Transformer, Loader, Filter, Bulker, DeBulker],
    attr_name: str,
    default: typing.Any = None,
):
    return getattr(node.configuration, attr_name, default)  # type: ignore
