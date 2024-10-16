# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import ctypes
import logging
from typing import Any

from faebryk.core.cpp import faebryk_core_cpp as cpp
from faebryk.core.graphinterface import (
    Graph,
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import (
    Link,
    LinkDirect,
    LinkDirectConditional,
    LinkDirectDerived,
    LinkNamedParent,
    LinkParent,
    LinkSibling,
)
from faebryk.core.module import Module
from faebryk.core.moduleinterface import GraphInterfaceModuleConnection, ModuleInterface
from faebryk.core.node import GraphInterfaceHierarchicalNode, Node
from faebryk.libs.util import DefaultFactoryDict, cast_assert

logger = logging.getLogger(__name__)


class CGraph:
    # TODO use other path
    class Path:
        def __init__(self, cpath: cpp.Path):
            self.gifs = [CGraph.gif_py(cgif) for cgif in cpath.gifs]

    def __init__(self, g: Graph):
        self.cg = cpp.Graph()
        self.gif_c: dict[GraphInterface, cpp.GraphInterface] = DefaultFactoryDict(
            self.create_cgif_from_gif
        )
        self.link_c: dict[Link, cpp.Link] = DefaultFactoryDict(
            self.create_clink_from_link
        )
        self.node_c: dict[Node, cpp.Node] = DefaultFactoryDict(
            self.create_cnode_from_node
        )

        def get_gif(gif: GraphInterface):
            c_gif = self.gif_c[gif]
            assert gif.node is not None
            c_gif.set_node(self.node_c[gif.node])
            return c_gif

        edges = [
            (get_gif(src), get_gif(dst), self.link_c[link])
            for src, dst, link in g.edges
        ]

        logger.info(f"Converting {g} -> V: {len(self.gif_c)} E: {len(edges)}")
        self.cg.add_edges(edges)

    @staticmethod
    def get_obj[T: Any](typ: type[T], ptr: int) -> T:
        return cast_assert(typ, ctypes.cast(ptr, ctypes.py_object).value)

    @staticmethod
    def gif_py(cgif: cpp.GraphInterface) -> GraphInterface:
        return CGraph.get_obj(GraphInterface, int(cgif.py_ptr))

    def create_cnode_from_node(self, node: Node) -> cpp.Node:
        if type(node) is Node:
            node_type = cpp.NodeType.GENERIC
        elif isinstance(node, Module):
            node_type = cpp.NodeType.MODULE
        elif isinstance(node, ModuleInterface):
            node_type = cpp.NodeType.MODULEINTERFACE
        else:
            node_type = cpp.NodeType.OTHER

        cgif = self.gif_c[node.self_gif]

        cnode = cpp.Node(
            node.get_name(accept_no_parent=True),
            type(node).__name__,
            node_type,
            id(node),
            cgif,
        )

        cgif.set_node(cnode)

        return cnode

    def create_cgif_from_gif(self, gif: GraphInterface) -> cpp.GraphInterface:
        cgif_type = {
            GraphInterface: cpp.GraphInterfaceType.GENERIC,
            GraphInterfaceHierarchical: cpp.GraphInterfaceType.HIERARCHICAL,
            GraphInterfaceSelf: cpp.GraphInterfaceType.SELF,
            GraphInterfaceHierarchicalNode: cpp.GraphInterfaceType.HIERARCHICAL_NODE,
            GraphInterfaceModuleConnection: cpp.GraphInterfaceType.MODULE_CONNECTION,
        }.get(type(gif), cpp.GraphInterfaceType.OTHER)

        return cpp.GraphInterface(
            cgif_type,
            id(gif),
            self.cg,
        )

    @staticmethod
    def create_clink_from_link(link: Link) -> cpp.Link:
        clink_type = {
            Link: cpp.LinkType.GENERIC,
            LinkSibling: cpp.LinkType.SIBLING,
            LinkParent: cpp.LinkType.PARENT,
            LinkNamedParent: cpp.LinkType.NAMED_PARENT,
            LinkDirect: cpp.LinkType.DIRECT,
            LinkDirectConditional: cpp.LinkType.DIRECT_CONDITIONAL,
            LinkDirectDerived: cpp.LinkType.DIRECT_DERIVED,
        }.get(type(link), cpp.LinkType.OTHER)

        return cpp.Link(clink_type, id(link))

    def find_paths(self, src: ModuleInterface, *dst: ModuleInterface):
        cpaths = cpp.find_paths(
            self.cg, self.node_c[src], [self.node_c[d] for d in dst]
        )
        return [self.Path(cpath) for cpath in cpaths]
