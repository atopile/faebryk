# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


def test_add():
    from faebryk.core.cpp import add

    assert add(1, 2) == 3
    assert add(1) == 2


def test_cnodes():
    from faebryk.core.cpp import LinkNamedParent, Node

    n1 = Node()
    n2 = Node()

    n1.children.connect(n2.parent, LinkNamedParent("test"))
    print(n2)
    print(n1)


def test_cobject():
    from faebryk.core.cpp import (
        GraphInterface,
        GraphInterfaceHierarchical,
        GraphInterfaceSelf,
        LinkDirect,
        LinkNamedParent,
    )

    g1 = GraphInterfaceSelf()
    g2 = GraphInterfaceHierarchical(True)
    g3 = GraphInterface()
    g4 = GraphInterfaceHierarchical(False)

    g2.connect(g3)
    g1.connect(g2, LinkDirect())
    g2.connect(g4, LinkNamedParent("test"))

    print(g1.edges)
    print(g2.edges)
    print(g1.get_graph())

    g1.get_graph().invalidate()


if __name__ == "__main__":
    test_cnodes()
