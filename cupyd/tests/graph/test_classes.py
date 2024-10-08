import pytest

from cupyd.core.exceptions import (
    NodesConnectionError,
    CyclicNodeError,
    NodesAlreadyConnectedError,
)


def test__simple_connection(node_a, node_b, node_c):
    node_a >> node_b >> node_c

    assert node_a.input is None
    assert node_b.input == node_a
    assert node_c.input == node_b

    assert node_a.outputs == [node_b]
    assert node_b.outputs == [node_c]
    assert node_c.outputs == []


def test__branched_connection(node_a, node_b, node_c):
    node_a >> [node_b, node_c]

    assert node_a.input is None
    assert node_b.input == node_a
    assert node_c.input == node_a

    assert node_a.outputs == [node_b, node_c]
    assert node_b.outputs == []
    assert node_c.outputs == []


def test__mixed_connection(node_a, node_b, node_c, node_d):
    node_a >> [node_b, node_c >> node_d]

    assert node_a.input is None
    assert node_b.input == node_a
    assert node_c.input == node_a
    assert node_d.input == node_c

    assert node_a.outputs == [node_b, node_c]
    assert node_b.outputs == []
    assert node_c.outputs == [node_d]
    assert node_d.outputs == []


def test__subgraph_left_connection(node_a, node_b, node_c, node_d):
    subgraph_1 = node_a >> [node_b, node_c]

    assert subgraph_1.root_node == node_a
    assert subgraph_1.leaf_nodes == (node_b, node_c)

    assert node_a.input is None
    assert node_b.input == node_a
    assert node_c.input == node_a
    assert node_d.input is None

    assert node_a.outputs == [node_b, node_c]
    assert node_b.outputs == []
    assert node_c.outputs == []
    assert node_d.outputs == []

    subgraph_2 = node_d >> subgraph_1

    assert subgraph_2.root_node == node_d
    assert subgraph_2.leaf_nodes == subgraph_1.leaf_nodes == (node_b, node_c)

    assert node_a.input == node_d
    assert node_d.input is None
    assert node_d.outputs == [node_a]

    assert node_a.outputs == [node_b, node_c]
    assert node_b.outputs == []
    assert node_c.outputs == []


def test__subgraph_right_connection(node_a, node_b, node_c, node_d):
    subgraph_1 = node_a >> node_b
    subgraph_2 = subgraph_1 >> node_c >> node_d

    assert subgraph_1.root_node == node_a
    assert subgraph_1.leaf_nodes == (node_b,)

    assert subgraph_2.root_node == node_a
    assert subgraph_2.leaf_nodes == (node_d,)


def test__nodes_connection_error(node_a, node_b, node_c, node_d):
    subgraph_1 = node_a >> [node_b, node_c]
    with pytest.raises(NodesConnectionError):
        subgraph_1 >> node_d


def test__cyclic_connection_error(node_a):
    with pytest.raises(CyclicNodeError):
        node_a >> node_a


def test__nodes_already_connected_error(node_a, node_b):
    with pytest.raises(NodesAlreadyConnectedError):
        node_a >> node_b
        node_a >> node_b


def test__node_input_already_connected_error(node_a, node_b, node_c):
    with pytest.raises(NodesConnectionError):
        node_a >> node_b
        _ = node_c >> node_b
