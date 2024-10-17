# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import itertools
import logging
from collections import defaultdict, deque
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
        visited_ref: dict[GraphInterface, Any],
    ) -> None:
        self.path: list[GraphInterface] = path
        self.visited_ref: dict[GraphInterface, Any] = visited_ref
        self.confidence = 1.0
        self.filtered = False
        self.path_data: dict[str, Any] = {}
        self.stop = False

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
        out.stop = base.stop
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
        # TODO
        for node in self.path:
            self.visited_ref[node] = [self]
        # self.visited_ref.update(self.path)


def insert_sorted(target: deque | list, item, key, asc=True):
    for i, p in enumerate(target):
        if (asc and key(item) < key(p)) or (not asc and key(item) > key(p)):
            target.insert(i, item)
            return i
    target.append(item)
    return len(target) - 1


def bfs_visit(
    roots: Iterable[GraphInterface],
) -> Generator[BFSPath, None, None]:
    """
    Generic BFS (not depending on Graph)
    Returns all visited nodes.
    """

    visited: defaultdict[GraphInterface, list[BFSPath]] = defaultdict(list)
    open_path_queue: deque[BFSPath] = deque()

    def handle_path(path: BFSPath):
        if path.stop:
            open_path_queue.clear()
            return

        if path.filtered:
            return

        # old_paths = visited[path.last]

        # promise_cnt = path.path_data.get("promise_depth", 0)
        # for p in old_paths:
        #    p_cnt = p.path_data.get("promise_depth", 0)
        # if promise_cnt > p_cnt:
        #    print("Pruned")
        #    return

        # def metric(x: BFSPath):
        #     # promise_cnt = x.path_data.get("promise_depth", 0)
        #     return (1 - x.confidence), len(x)

        # insert_sorted(old_paths, path, key=metric)
        visited[path.last]
        if path.strong:
            path.mark_visited()

        # insert_sorted(open_path_queue, path, key=lambda x: (len(x), (1 - x.confidence)))
        open_path_queue.append(path)

    # yield identity paths
    for root in roots:
        path = BFSPath([root], visited)
        yield path
        handle_path(path)

    while open_path_queue:
        open_path = open_path_queue.popleft()

        edges = set(open_path.last.edges)
        for neighbour in edges:
            # visited
            if neighbour in visited:
                # complete path
                if any(x.strong for x in visited[neighbour]):
                    continue
                # visited in path (loop)
                if neighbour in open_path:
                    continue

            new_path = open_path + neighbour

            yield new_path
            handle_path(new_path)
