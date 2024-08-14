# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, Iterable, Iterator, Mapping, Self

# import igraph as ig
import graph_tool.all as gt
import networkx as nx
from faebryk.libs.util import SharedReference, bfs_visit
from typing_extensions import deprecated

logger = logging.getLogger(__name__)

# only for typechecker

if TYPE_CHECKING:
    from faebryk.core.core import Link

# TODO create GraphView base class


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

    def bfs_visit(
        self, filter: Callable[[T], bool], start: Iterable[T], G: GT | None = None
    ):
        G = G or self()

        return bfs_visit(lambda n: [o for o in self.get_edges(n) if filter(o)], start)

    def __str__(self) -> str:
        return f"{type(self).__name__}(V={self.node_cnt}, E={self.edge_cnt})"

    @abstractmethod
    def __iter__(self) -> Iterator[T]: ...

    # TODO subgraph should return a new GraphView
    @abstractmethod
    def subgraph(self, node_filter: Callable[[T], bool]) -> Iterable[T]: ...

    def subgraph_type(self, *types: type[T]):
        return self.subgraph(lambda n: isinstance(n, types))


class GraphNX[T](Graph[T, nx.Graph]):
    GI = nx.Graph

    def __init__(self):
        super().__init__(nx.Graph())

    @property
    def node_cnt(self) -> int:
        return len(self())

    @property
    def edge_cnt(self) -> int:
        return self().size()

    def v(self, obj: T):
        return obj

    def add_edge(self, from_obj: T, to_obj: T, link: "Link"):
        self().add_edge(from_obj, to_obj, link=link)

    def is_connected(self, from_obj: T, to_obj: T) -> "Link | None":
        return self.get_edges(from_obj).get(to_obj)

    def get_edges(self, obj: T) -> Mapping[T, "Link"]:
        return {other: d["link"] for other, d in self().adj.get(obj, {}).items()}

    def bfs_visit(self, filter: Callable[[T], bool], start: Iterable[T], G=None):
        # nx impl, >3x slower
        # fG = nx.subgraph_view(G, filter_node=filter)
        # return [o for _, o in nx.bfs_edges(fG, start[0])]
        return super().bfs_visit(filter, start, G)

    @staticmethod
    def _union(rep: nx.Graph, old: nx.Graph):
        # merge big into small
        if len(old.nodes) > len(rep.nodes):
            rep, old = old, rep

        # print(f"union: {len(rep.nodes)=} {len(old.nodes)=}")
        rep.update(old)

        return rep

    def subgraph(self, node_filter: Callable[[T], bool]):
        return nx.subgraph_view(self(), filter_node=node_filter)

    def __repr__(self) -> str:
        from textwrap import dedent

        return dedent(f"""
            {type(self).__name__}(
                {self.graph_repr(self())}
            )
        """)

    @staticmethod
    def graph_repr(G: nx.Graph) -> str:
        from textwrap import dedent, indent

        nodes = indent("\n".join(f"{k}" for k in G.nodes), " " * 4 * 5)
        longest_node_name = max(len(str(k)) for k in G.nodes)

        def edge_repr(u, v, d) -> str:
            if "link" not in d:
                link = ""
            else:
                link = f"({type(d['link']).__name__})"
            return f"{str(u)+' ':-<{longest_node_name+1}}--{link:-^20}" f"--> {v}"

        edges = indent(
            "\n".join(edge_repr(u, v, d) for u, v, d in G.edges(data=True)),
            " " * 4 * 5,
        )

        return dedent(f"""
            Nodes ----- {len(G)}\n{nodes}
            Edges ----- {G.size()}\n{edges}
        """)

    def __iter__(self) -> Iterator[T]:
        return iter(self())


class GraphGT[T](Graph[T, gt.Graph]):
    GI = gt.Graph

    def __init__(self):
        G = gt.Graph(directed=False)
        super().__init__(G)
        G.vp["KV"] = G.new_vertex_property("object")
        lookup: dict[T, int] = {}
        G.gp["VK"] = G.new_graph_property("object", lookup)
        G.ep["L"] = G.new_edge_property("object")

    @property
    def node_cnt(self) -> int:
        return self().num_vertices()

    @property
    def edge_cnt(self) -> int:
        return self().num_edges()

    def v(self, obj: T):
        v_i = self().gp["VK"].get(obj)
        if v_i is not None:
            return self().vertex(v_i)

        v = self().add_vertex()
        v_i = self().vertex_index[v]
        self().vp["KV"][v] = obj
        self().gp["VK"][obj] = v_i
        return v

    def _v_to_obj(self, v: gt.VertexBase | int) -> T:
        return self().vp["KV"][v]

    def _as_graph_vertex_func[O](
        self, f: Callable[[T], O]
    ) -> Callable[[gt.VertexBase | int], O]:
        return lambda v: f(self._v_to_obj(v))

    def add_edge(self, from_obj: T, to_obj: T, link: "Link"):
        from_v = self.v(from_obj)
        to_v = self.v(to_obj)
        e = self().add_edge(from_v, to_v, add_missing=False)
        self().ep["L"][e] = link

    def is_connected(self, from_obj: T, to_obj: T) -> "Link | None":
        from_v = self.v(from_obj)
        to_v = self.v(to_obj)
        e = self().edge(from_v, to_v, add_missing=False)
        if not e:
            return None
        return self().ep["L"][e]

    def get_edges(self, obj: T) -> Mapping[T, "Link"]:
        v = self.v(obj)
        v_i = self().vertex_index[v]

        def other(v_i_l, v_i_r):
            return v_i_l if v_i_r == v_i else v_i_r

        return {
            self._v_to_obj(other(v_i_l, v_i_r)): self().ep["L"][e_i]
            for v_i_l, v_i_r, e_i in self().get_all_edges(v, [self().edge_index])
        }

    @staticmethod
    def _union(g1: gt.Graph, g2: gt.Graph) -> gt.Graph:
        v_is = len(g1.get_vertices())
        gt.graph_union(
            g1,
            g2,
            internal_props=True,
            include=True,
            props=[
                (g1.vp["KV"], g2.vp["KV"]),
                (g1.ep["L"], g2.ep["L"]),
            ],
        )
        g1.gp["VK"].update({k: v + v_is for k, v in g2.gp["VK"].items()})

        return g1

    def bfs_visit(
        self, filter: Callable[[T], bool], start: Iterable[T], G: gt.Graph | None = None
    ):
        # TODO implement with gt bfs
        return super().bfs_visit(filter, start, G)

    def _iter(self, g: gt.Graph):
        return (self._v_to_obj(v) for v in g.iter_vertices())

    def __iter__(self) -> Iterator[T]:
        return self._iter(self())

    def subgraph(self, node_filter: Callable[[T], bool]):
        return self._iter(
            gt.GraphView(self(), vfilt=self._as_graph_vertex_func(node_filter))
        )


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
