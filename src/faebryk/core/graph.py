# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import TYPE_CHECKING, Any, Self

import networkx as nx
from faebryk.libs.util import SharedReference
from typing_extensions import deprecated

logger = logging.getLogger(__name__)

# only for typechecker

if TYPE_CHECKING:
    from faebryk.core.core import Link


class Graph(SharedReference[nx.Graph]):
    def __init__(self):
        super().__init__(nx.Graph())

    @staticmethod
    def get_link_from_edge(edge: dict[str, Any]) -> "Link":
        return edge["link"]

    @property
    @deprecated("Use call")
    def G(self):
        return self()

    def merge(self, other: Self) -> Self:
        res = self.link(other)
        if not res:
            return self

        res.object.update(res.old)

        # TODO remove, should not be needed
        assert isinstance(res.representative, type(self))

        return res.representative

    def __repr__(self) -> str:
        G = self()
        node_cnt = len(G.nodes)
        edge_cnt = len(G.edges)
        g_repr = f"{type(G).__name__}({node_cnt=},{edge_cnt=})({hex(id(G))})"
        return f"{type(self).__name__}({g_repr})"
