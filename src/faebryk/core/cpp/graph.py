# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import ctypes
import logging
from itertools import pairwise
from typing import Any, Iterable

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
from faebryk.core.moduleinterface import (
    GraphInterfaceHierarchicalModuleSpecial,
    GraphInterfaceModuleConnection,
    ModuleInterface,
)
from faebryk.core.node import GraphInterfaceHierarchicalNode, Node
from faebryk.libs.util import DefaultFactoryDict, NotNone, cast_assert

logger = logging.getLogger(__name__)


class CGraph:
    _cache: "CGraph | None" = None
    _cache_edge_cnt: int | None = None

    # TODO use other path
    class Path:
        def __init__(self, cpath: cpp.Path):
            self.path = [CGraph.gif_py(cgif) for cgif in cpath.gifs]

        @property
        def last(self) -> GraphInterface:
            return self.path[-1]

        @property
        def edges(self) -> Iterable[tuple[GraphInterface, GraphInterface]]:
            return pairwise(self.path)

    def __new__(cls, g: Graph):
        if cls._cache is None or cls._cache_edge_cnt != g.edge_cnt:
            cls._cache = super().__new__(cls)
            cls._cache.setup(g)
            cls._cache_edge_cnt = g.edge_cnt
        return cls._cache

    def setup(self, g: Graph):
        self.cg = cpp.Graph()
        self._gif_c: dict[GraphInterface, cpp.GraphInterface] = DefaultFactoryDict(
            self.create_cgif_from_gif
        )
        self.link_c: dict[Link, cpp.Link] = DefaultFactoryDict(
            self.create_clink_from_link
        )
        self.node_c: dict[Node, cpp.Node] = DefaultFactoryDict(
            self.create_cnode_from_node
        )

        edges = [
            (self.get_gif(src), self.get_gif(dst), self.link_c[link])
            for src, dst, link in g.edges
            # TODO remove, preoptimization that only works for mifs
            if isinstance(src.node, ModuleInterface)
            and isinstance(dst.node, ModuleInterface)
            and type(src)
            in {
                GraphInterfaceSelf,
                GraphInterfaceHierarchicalModuleSpecial,
                GraphInterfaceModuleConnection,
                GraphInterfaceHierarchicalNode,
            }
        ]

        logger.info(f"Converting {g} -> V: {len(self._gif_c)} E: {len(edges)}")
        self.cg.add_edges(edges)

    def get_gif(self, gif: GraphInterface):
        c_gif = self._gif_c[gif]
        assert gif.node is not None
        c_gif.set_node(self.node_c[gif.node])
        return c_gif

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

        cgif = self._gif_c[node.self_gif]

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
            GraphInterfaceHierarchicalModuleSpecial: cpp.GraphInterfaceType.HIERARCHICAL_MODULE_SPECIAL,
            GraphInterfaceModuleConnection: cpp.GraphInterfaceType.MODULE_CONNECTION,
        }.get(type(gif), cpp.GraphInterfaceType.OTHER)

        cgif = cpp.GraphInterface(
            cgif_type,
            id(gif),
            self.cg,
        )

        if isinstance(gif, GraphInterfaceHierarchical):
            # TODO this happens for unconnected hierarchical gifs
            # e.g specializes of moduleinterfaces
            # need a better way to handle, for now we just dont mark them hierarchical
            # which is valid in the context of pathfinding
            if not gif.is_parent and gif.get_parent() is None:
                return cgif
            cgif.make_hierarchical(
                gif.is_parent,
                NotNone(gif.get_parent())[1] if not gif.is_parent else "",
            )

        return cgif

    @staticmethod
    def create_clink_from_link(link: Link) -> cpp.Link:
        clink_type = {
            Link: cpp.LinkType.GENERIC,
            LinkSibling: cpp.LinkType.SIBLING,
            LinkParent: cpp.LinkType.PARENT,
            LinkNamedParent: cpp.LinkType.NAMED_PARENT,
            LinkDirect: cpp.LinkType.DIRECT,
            LinkDirectConditional: cpp.LinkType.DIRECT_CONDITIONAL,
            ModuleInterface.LinkDirectShallow: cpp.LinkType.DIRECT_CONDITIONAL_SHALLOW,
            LinkDirectDerived: cpp.LinkType.DIRECT_DERIVED,
        }.get(type(link), cpp.LinkType.OTHER)

        filters = []
        if isinstance(link, ModuleInterface.LinkDirectShallow):
            clink_type = cpp.LinkType.DIRECT_CONDITIONAL_SHALLOW
            filters = [t.__name__ for t in link._children_types]
        elif isinstance(link, LinkDirectConditional):
            raise NotImplementedError(f"Link type not implemented in C++: {link}")

        if isinstance(link, LinkNamedParent):
            clink_type = cpp.LinkType.NAMED_PARENT

        if clink_type == cpp.LinkType.OTHER:
            raise NotImplementedError(f"Link type not implemented in C++: {link}")

        return cpp.Link(clink_type, id(link), filters)

    def find_paths(self, src: ModuleInterface, *dst: ModuleInterface):
        cpaths, counters = cpp.find_paths(
            self.cg, self.node_c[src], [self.node_c[d] for d in dst]
        )
        return [self.Path(cpath) for cpath in cpaths], counters
