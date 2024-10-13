from pytest import fixture

from cupyd.core.graph.classes import Node


@fixture(scope="function", autouse=True)
def node_a():
    node = Node()
    node.name = "A"
    yield node


@fixture(scope="function", autouse=True)
def node_b():
    node = Node()
    node.name = "B"
    yield node


@fixture(scope="function", autouse=True)
def node_c():
    node = Node()
    node.name = "C"
    yield node


@fixture(scope="function", autouse=True)
def node_d():
    node = Node()
    node.name = "D"
    yield node


@fixture(scope="function", autouse=True)
def node_e():
    node = Node()
    node.name = "E"
    yield node


@fixture(scope="function", autouse=True)
def node_f():
    node = Node()
    node.name = "F"
    yield node


@fixture(scope="function", autouse=True)
def node_g():
    node = Node()
    node.name = "G"
    yield node


@fixture(scope="function", autouse=True)
def node_h():
    node = Node()
    node.name = "H"
    yield node


@fixture(scope="function", autouse=True)
def node_i():
    node = Node()
    node.name = "i"
    yield node
