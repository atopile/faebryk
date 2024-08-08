# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Mapping, Self

# import igraph as ig
import networkx as nx
from faebryk.libs.util import SharedReference
from typing_extensions import deprecated

logger = logging.getLogger(__name__)

# only for typechecker

if TYPE_CHECKING:
    from faebryk.core.core import Link


class Graph[T, GT](SharedReference[GT]):
    @property
    @deprecated("Use call")
    def G(self):
        return self()

    def merge(self, other: Self) -> tuple[Self, bool]:
        if self() == other():
            return self, False

        unioned = self._union(self(), other())
        lhs, rhs = self, other
        if unioned is rhs():
            lhs, rhs = rhs, lhs
        if unioned is not lhs():
            lhs.set(unioned)

        res = lhs.link(rhs)
        if not res:
            return self, False

        # TODO remove, should not be needed
        assert isinstance(res.representative, type(self))

        return res.representative, True

    def __repr__(self) -> str:
        G = self()
        node_cnt = self.node_cnt
        edge_cnt = self.edge_cnt
        g_repr = f"{type(G).__name__}({node_cnt=},{edge_cnt=})({hex(id(G))})"
        return f"{type(self).__name__}({g_repr})"

    @property
    @abstractmethod
    def node_cnt(self) -> int: ...

    @property
    @abstractmethod
    def edge_cnt(self) -> int: ...

    @abstractmethod
    def v(self, obj: T): ...

    @abstractmethod
    def add_edge(self, from_obj: T, to_obj: T, link: "Link"): ...

    @abstractmethod
    def is_connected(self, from_obj: T, to_obj: T) -> "Link | None": ...

    @abstractmethod
    def get_edges(self, obj: T) -> Mapping[T, "Link"]: ...

    @staticmethod
    @abstractmethod
    def _union(rep: GT, old: GT) -> GT: ...

    def __str__(self) -> str:
        return f"{type(self).__name__}(V={self.node_cnt}, E={self.edge_cnt})"


class GraphNX[T](Graph[T, nx.Graph]):
    def __init__(self):
        super().__init__(nx.Graph())

    @property
    def node_cnt(self) -> int:
        return len(self().nodes)

    @property
    def edge_cnt(self) -> int:
        return len(self().edges)

    def v(self, obj: T):
        return obj

    def add_edge(self, from_obj: T, to_obj: T, link: "Link"):
        self().add_edge(from_obj, to_obj, link=link)

    def is_connected(self, from_obj: T, to_obj: T) -> "Link | None":
        return self.get_edges(from_obj).get(to_obj)

    def get_edges(self, obj: T) -> Mapping[T, "Link"]:
        return {other: d["link"] for other, d in self().adj.get(obj, {}).items()}

    @staticmethod
    def _union(rep: nx.Graph, old: nx.Graph):
        # merge big into small
        if len(old.nodes) > len(rep.nodes):
            rep, old = old, rep

        # print(f"union: {len(rep.nodes)=} {len(old.nodes)=}")
        rep.update(old)

        return rep

    def __repr__(self) -> str:
        from textwrap import dedent, indent

        nodes = indent("\n".join(f"{k}" for k in self().nodes), " " * 4 * 5)
        longest_node_name = max(len(str(k)) for k in self().nodes)
        edges = indent(
            "\n".join(
                f"{str(k)+' ':-<{longest_node_name+1}}--{type(d['link']).__name__:-^20}"
                f"--> {v}"
                for k, v, d in self().edges(data=True)
            ),
            " " * 4 * 5,
        )

        return dedent(f"""
            {type(self).__name__}(
                Nodes ----- {self.node_cnt}\n{nodes}
                Edges ----- {self.edge_cnt}\n{edges}
            )
        """)


# class GraphIG[T](Graph[T, ig.Graph]):
#     # Notes:
#     # - union is slow
#     # - add_edge is slowish
#
#     def __init__(self):
#         super().__init__(ig.Graph(vertex_attrs={"name": "name"}))
#
#     @property
#     def node_cnt(self) -> int:
#         return len(self().vs)
#
#     @property
#     def edge_cnt(self) -> int:
#         return len(self().es)
#
#     def v(self, obj: T, add=False) -> ig.Vertex:
#         out = str(id(obj))
#         if add and out not in self().vs["name"]:
#             return self().add_vertex(name=out, obj=obj)
#         return out
#
#     def add_edge(self, from_obj: T, to_obj: T, link: "Link") -> ig.Edge:
#         from_v = self.v(from_obj, True)
#         to_v = self.v(to_obj, True)
#         return self().add_edge(from_v, to_v, link=link)
#
#     def is_connected(self, from_obj: T, to_obj: T) -> "Link | None":
#         try:
#             v_from = self().vs.find(name=self.v(from_obj))
#             v_to = self().vs.find(name=self.v(to_obj))
#         except ValueError:
#             return None
#         edge = self().es.select(_source=v_from, _target=v_to)
#         if not edge:
#             return None
#
#         return edge[0]["link"]
#
#     def get_edges(self, obj: T) -> Mapping[T, "Link"]:
#         edges = self().es.select(_source=self.v(obj))
#         return {self().vs[edge.target]["name"]: edge["link"] for edge in edges}
#
#     @staticmethod
#     def _union(rep: ig.Graph, old: ig.Graph):
#         return rep + old  # faster, but correct?
