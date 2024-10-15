# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import copy
import itertools
import logging
from collections import deque
from typing import Any, Generator, Iterable, Self

from faebryk.core.graphinterface import GraphInterface
from faebryk.core.link import Link
from faebryk.libs.util import DefaultFactoryDict

logger = logging.getLogger(__name__)


class BFSPath:
    link_cache: dict[tuple[GraphInterface, GraphInterface], Link] = DefaultFactoryDict(
        lambda x: x[0].is_connected_to(x[1])
    )

    def __init__(
        self,
        path: list[GraphInterface],
        visited_ref: set[GraphInterface],
    ) -> None:
        self.path: list[GraphInterface] = path
        self.visited_ref: set[GraphInterface] = visited_ref
        self.confidence = 1.0
        self.filtered = False
        self.path_data: dict[str, Any] = {}

    @property
    def last(self) -> GraphInterface:
        return self.path[-1]

    def get_link(self, edge: tuple[GraphInterface, GraphInterface]) -> Link:
        return self.link_cache[edge]

    @property
    def last_edge(self) -> tuple[GraphInterface, GraphInterface] | None:
        if len(self.path) < 2:
            return None
        return self.path[-2], self.path[-1]

    @property
    def first(self) -> GraphInterface:
        return self.path[0]

    @classmethod
    def from_base(cls, base: "BFSPath", node: GraphInterface):
        out = cls(
            base.path + [node],
            visited_ref=base.visited_ref,
        )
        out.confidence = base.confidence
        out.filtered = base.filtered
        out.path_data = base.path_data
        return out

    def __add__(self, node: GraphInterface) -> Self:
        return self.from_base(self, node)

    def __contains__(self, node: GraphInterface) -> bool:
        return node in self.path

    @property
    def edges(self) -> Iterable[tuple[GraphInterface, GraphInterface]]:
        return itertools.pairwise(self.path)

    def __len__(self) -> int:
        return len(self.path)

    def __getitem__(self, idx: int) -> GraphInterface:
        return self.path[idx]

    # The partial visit stuff is pretty weird, let me try to explain:
    # If a node is not fully visited through a path, it means that there might still
    # be paths that lead to this node that are more interesting. Thus we give the caller
    # the chance to explore those other paths.
    # If at a later point the caller discovers that the current path is fully visited
    # after all, it can mark it.
    @property
    def strong(self) -> bool:
        return self.confidence == 1.0

    def mark_visited(self):
        self.visited_ref.update(self.path)


def bfs_visit(
    roots: Iterable[GraphInterface],
) -> Generator[BFSPath, None, None]:
    """
    Generic BFS (not depending on Graph)
    Returns all visited nodes.
    """

    visited: set[GraphInterface] = set()
    visited_partially: set[GraphInterface] = set()
    open_path_queue: deque[BFSPath] = deque()
    open_path_queue_weak: deque[BFSPath] = deque()

    def handle_path(path: BFSPath):
        if path.filtered:
            return
        visited_partially.add(path.last)
        if path.strong:
            path.mark_visited()
            open_path_queue.append(path)
        else:
            open_path_queue_weak.append(path)

    # yield identity paths
    for root in roots:
        path = BFSPath([root], visited)
        yield path
        handle_path(path)

    while open_path_queue or open_path_queue_weak:
        if open_path_queue:
            open_path = open_path_queue.popleft()
        else:
            open_path = open_path_queue_weak.popleft()

        edges = set(open_path.last.edges)
        for neighbour in edges:
            # visited
            if neighbour in visited:
                continue
            # visited in path (loop)
            if neighbour in visited_partially and neighbour in open_path:
                continue

            new_path = open_path + neighbour

            yield new_path
            handle_path(new_path)
