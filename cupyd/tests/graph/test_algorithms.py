from cupyd.core.graph.algorithms import topological_sort
from cupyd.core.graph.classes import Edge


def test__topological_sort(node_a, node_b, node_c, node_d, node_e, node_f, node_g, node_h, node_i):
    node_a >> node_e >> node_f >> [node_g >> node_h >> node_b, node_d]
    # no need to assign to anything but just to avoid warning on newer python versions (>= 3.12)
    _ = node_e >> node_c
    _ = node_f >> node_i

    nodes, edges = topological_sort(root_node=node_a)

    assert nodes == [
        node_a,
        node_e,
        node_f,
        node_g,
        node_h,
        node_b,
        node_d,
        node_i,
        node_c,
    ]
    assert edges == [
        Edge(node_a, node_e),
        Edge(node_e, node_f),
        Edge(node_f, node_g),
        Edge(node_g, node_h),
        Edge(node_h, node_b),
        Edge(node_f, node_d),
        Edge(node_f, node_i),
        Edge(node_e, node_c),
    ]
