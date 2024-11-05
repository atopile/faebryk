# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from abc import abstractmethod


def test_add():
    from faebryk.core.cpp import add, call_python_function

    assert add(1, 2) == 3
    assert add(1) == 2

    assert call_python_function(lambda: 1) == 1


def test_cnodes():
    from faebryk.core.cpp import LinkNamedParent, Node

    n1 = Node()
    n1.transfer_ownership(n1)
    n2 = Node()
    n2.transfer_ownership(n2)

    class _Node(Node):
        def __init__(self) -> None:
            super().__init__()
            self.transfer_ownership(self)

    n3 = _Node()

    n1.children.connect(n2.parent, LinkNamedParent("test"))
    print(n2)
    print(n1)
    print(n3)
    print(n1.children.get_children())


def test_pynode():
    from faebryk.core.node import Node

    n = Node()
    print(n)
    print("---")

    class SubNode(Node):
        a: Node
        b: Node

    sn = SubNode()
    print(sn.a)

    print(sn.get_children(direct_only=True, types=Node))


def test_derived_pynodes():
    from faebryk.core.module import Module
    from faebryk.core.moduleinterface import ModuleInterface

    class App(Module):
        mif1: ModuleInterface
        mif2: ModuleInterface

    app = App()
    app.mif1.connect(app.mif2)

    print(app.mif1)
    print(app.mif1.get_connected())


def test_traits_basic():
    from faebryk.core.node import Node
    from faebryk.core.trait import Trait

    class T(Trait):
        @abstractmethod
        def do(self): ...

    class T_do(T.impl()):
        def do(self):
            print("do")

    class A(Node):
        t: T_do

    a = A()

    print(a.t)
    print(a.get_trait(T))
    a.get_trait(T).do()


def test_library_nodes():
    import faebryk.library._F as F

    x = F.Electrical()

    print(x)


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
    # test_add()
    # test_cobject()
    # test_cnodes()
    # test_pynode()
    test_derived_pynodes()
