# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import unittest

from faebryk.core.cpp import (
    GraphInterface,
    GraphInterfaceHierarchical,
    LinkExists,
    LinkNamedParent,
)
from faebryk.core.link import (
    LinkDirect,
    LinkDirectConditional,
    LinkDirectConditionalFilterResult,
    LinkParent,
    LinkSibling,
)
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.libs.library import L


class TestGraph(unittest.TestCase):
    def test_gifs(self):
        from faebryk.core.graphinterface import GraphInterface as GIF

        gif1 = GIF()
        gif2 = GIF()

        gif1.connect(gif2)

        self.assertIn(gif2, gif1.edges)
        self.assertTrue(gif1.is_connected_to(gif2))

        gif3 = GIF()

        class linkcls(LinkDirect):
            pass

        gif1.connect(gif3, linkcls())
        self.assertIsInstance(gif1.is_connected_to(gif3), linkcls)
        self.assertEqual(gif1.is_connected_to(gif3), gif3.is_connected_to(gif1))

        self.assertRaises(LinkExists, lambda: gif1.connect(gif3))
        self.assertRaises(LinkExists, lambda: gif1.connect(gif3, linkcls()))

        self.assertEqual(gif1.G, gif2.G)

    def test_node_gifs(self):
        from faebryk.core.node import Node

        n1 = Node()

        self.assertIsInstance(n1.self_gif.is_connected_to(n1.parent), LinkSibling)
        self.assertIsInstance(n1.self_gif.is_connected_to(n1.children), LinkSibling)

        n2 = Node()
        n1.add(n2, name="n2")

        self.assertIsInstance(n1.children.is_connected_to(n2.parent), LinkParent)

        print(n1.get_graph())

        p = n2.get_parent()
        self.assertIsNotNone(p)
        assert p is not None
        self.assertIs(p[0], n1)

        self.assertEqual(n1.self_gif.G, n2.self_gif.G)

    # TODO move to own file
    def test_fab_ll_simple_hierarchy(self):
        class N(Node):
            SN1: Node
            SN2: Node
            SN3 = L.list_field(2, Node)

            @L.rt_field
            def SN4(self):
                return Node()

        n = N()
        children = n.get_children(direct_only=True, types=Node)
        self.assertEqual(children, {n.SN1, n.SN2, n.SN3[0], n.SN3[1], n.SN4})

    def test_fab_ll_chain_names(self):
        root = Node()
        x = root
        for i in range(10):
            y = Node()
            x.add(y, f"i{i}")
            x = y

        self.assertRegex(
            x.get_full_name(), "[*][0-9A-F]{4}.i0.i1.i2.i3.i4.i5.i6.i7.i8.i9"
        )

    def test_fab_ll_chain_tree(self):
        root = Node()
        x = root
        for i in range(10):
            y = Node()
            z = Node()
            x.add(y, f"i{i}")
            x.add(z, f"j{i}")
            x = y

        self.assertRegex(
            x.get_full_name(), "[*][0-9A-F]{4}.i0.i1.i2.i3.i4.i5.i6.i7.i8.i9"
        )

    def test_link_eq_direct(self):
        gif1 = GraphInterface()
        gif2 = GraphInterface()

        gif1.connect(gif2)

        self.assertEqual(gif1.is_connected_to(gif2), LinkDirect())
        self.assertNotEqual(gif1.is_connected_to(gif2), LinkSibling())

    def test_link_eq_args(self):
        gif1 = GraphInterfaceHierarchical(is_parent=True)
        gif2 = GraphInterfaceHierarchical(is_parent=False)

        gif1.connect(gif2, link=LinkNamedParent("bla"))

        self.assertEqual(gif1.is_connected_to(gif2), LinkNamedParent("bla"))
        self.assertNotEqual(gif1.is_connected_to(gif2), LinkNamedParent("blub"))
        self.assertNotEqual(gif1.is_connected_to(gif2), LinkDirect())

    def test_inherited_link(self):
        class _Link(LinkDirectConditional):
            def __init__(self):
                super().__init__(
                    lambda path: LinkDirectConditionalFilterResult.FILTER_PASS
                )

        gif1 = GraphInterface()
        gif2 = GraphInterface()

        gif1.connect(gif2, link=_Link())
        self.assertIsInstance(gif1.is_connected_to(gif2), _Link)

    def test_unique_mif_shallow_link(self):
        class MIFType(ModuleInterface):
            pass

        assert MIFType.LinkDirectShallow() is MIFType.LinkDirectShallow()


if __name__ == "__main__":
    unittest.main()
