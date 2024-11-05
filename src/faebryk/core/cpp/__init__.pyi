# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

# This file is auto-generated by nanobind.
# Do not edit this file directly; edit the corresponding
# C++ file instead.
from collections.abc import Callable, Sequence, Set
from typing import overload

class Graph:
    def __init__(self) -> None: ...
    def get_edges(self, arg: GraphInterface, /) -> dict[GraphInterface, Link]: ...
    def invalidate(self) -> None: ...
    @property
    def node_count(self) -> int: ...
    @property
    def edge_count(self) -> int: ...
    def node_projection(self) -> set[Node]: ...
    def nodes_by_names(self, arg: Set[str], /) -> list[tuple[Node, str]]: ...
    def bfs_visit(
        self,
        filter: Callable[[Sequence[GraphInterface], Link], bool],
        start: Sequence[GraphInterface],
    ) -> set[GraphInterface]: ...
    def __repr__(self) -> str: ...

class GraphInterface:
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...
    def get_graph(self) -> Graph: ...
    @property
    def G(self) -> Graph: ...
    def get_gif_edges(self) -> set[GraphInterface]: ...
    def get_direct_connections(self) -> set[GraphInterface]: ...
    @property
    def edges(self) -> dict[GraphInterface, Link]: ...
    @property
    def node(self) -> Node: ...
    @node.setter
    def node(self, arg: Node, /) -> None: ...
    def is_connected(self, arg: GraphInterface, /) -> Link | None: ...
    @property
    def name(self) -> str: ...
    @name.setter
    def name(self, arg: str, /) -> None: ...
    def get_connected_nodes(self, types: Sequence[type]) -> set[Node]: ...
    @overload
    def connect(self, arg: GraphInterface, /) -> None: ...
    @overload
    def connect(self, arg0: GraphInterface, arg1: Link, /) -> None: ...

class GraphInterfaceHierarchical(GraphInterface):
    def __init__(self, is_parent: bool) -> None: ...
    def get_parent(self) -> tuple[Node, str] | None: ...
    def get_children(self) -> list[tuple[Node, str]]: ...
    @property
    def is_parent(self) -> bool: ...
    def disconnect_parent(self) -> None: ...

class GraphInterfaceModuleConnection(GraphInterface):
    def __init__(self) -> None: ...

class GraphInterfaceModuleSibling(GraphInterfaceHierarchical):
    def __init__(self, is_parent: bool) -> None: ...

class GraphInterfaceReference(GraphInterface):
    def __init__(self) -> None: ...
    def get_referenced_gif(self) -> GraphInterfaceSelf: ...
    def get_reference(self) -> Node: ...

class GraphInterfaceReferenceUnboundError(Exception):
    pass

class GraphInterfaceSelf(GraphInterface):
    def __init__(self) -> None: ...

class Link:
    pass

class LinkDirect(Link):
    def __init__(self) -> None: ...

class LinkDirectConditional(LinkDirect):
    def __init__(
        self, arg: Callable[[GraphInterface, GraphInterface], bool], /
    ) -> None: ...

class LinkNamedParent(LinkParent):
    def __init__(self, arg: str, /) -> None: ...

class LinkParent(Link):
    def __init__(self) -> None: ...

class LinkPointer(Link):
    def __init__(self) -> None: ...

class LinkSibling(LinkPointer):
    def __init__(self) -> None: ...

class Node:
    def __init__(self) -> None: ...
    @staticmethod
    def transfer_ownership(arg: Node, /) -> Node: ...
    def get_graph(self) -> Graph: ...
    @property
    def self_gif(self) -> GraphInterfaceSelf: ...
    @property
    def children(self) -> GraphInterfaceHierarchical: ...
    @property
    def parent(self) -> GraphInterfaceHierarchical: ...
    def get_parent(self) -> tuple[Node, str] | None: ...
    def get_parent_force(self) -> tuple[Node, str]: ...
    def get_name(self) -> str: ...
    def get_hierarchy(self) -> list[tuple[Node, str]]: ...
    def get_full_name(self, types: bool = False) -> str: ...
    def set_py_handle(self, arg: object, /) -> None: ...
    def __repr__(self) -> str: ...

class NodeException(Exception):
    pass

class NodeNoParent(Exception):
    pass

def add(i: int, j: int = 1) -> int:
    """A function that adds two numbers"""

def call_python_function(func: Callable[[], int]) -> int: ...
def print_obj(obj: object) -> None: ...
def set_leak_warnings(value: bool) -> None: ...
