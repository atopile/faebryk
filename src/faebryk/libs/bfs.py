# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import itertools
import logging
from collections import deque
from typing import Callable, Generator, Iterable, Self

logger = logging.getLogger(__name__)


class BFSPath[T]:
    def __init__(self, path: list[T], visited_ref: set[T]) -> None:
        self.path: list[T] = path
        self.visited_ref: set[T] = visited_ref
        self._fully_visited = True

    @property
    def last(self) -> T:
        return self.path[-1]

    @property
    def first(self) -> T:
        return self.path[0]

    @classmethod
    def from_base(cls, base: "BFSPath[T]", node: T):
        return cls(base.path + [node], base.visited_ref)

    def __add__(self, node: T) -> Self:
        return self.from_base(self, node)

    def __contains__(self, node: T) -> bool:
        return node in self.path

    @property
    def edges(self) -> Iterable[tuple[T, T]]:
        return itertools.pairwise(self.path)

    def __len__(self) -> int:
        return len(self.path)

    def __getitem__(self, idx: int) -> T:
        return self.path[idx]

    # The partial visit stuff is pretty weird, let me try to explain:
    # If a node is not fully visited through a path, it means that there might still
    # be paths that lead to this node that are more interesting. Thus we give the caller
    # the chance to explore those other paths.
    # If at a later point the caller discovers that the current path is fully visited
    # after all, it can mark it.
    @property
    def fully_visited(self) -> bool:
        return self._fully_visited

    @fully_visited.setter
    def fully_visited(self, value: bool):
        self._fully_visited = value
        if value:
            self.mark_visited()

    def mark_visited(self):
        self.visited_ref.update(self.path)


def bfs_visit[T](
    neighbours: Callable[[BFSPath[T]], Iterable[BFSPath[T]]],
    roots: Iterable[T],
) -> Generator[BFSPath[T], None, None]:
    """
    Generic BFS (not depending on Graph)
    Returns all visited nodes.
    """
    visited: set[T] = set(roots)
    visited_partially: set[T] = set(roots)
    open_path_queue: deque[BFSPath[T]] = deque(
        [BFSPath([root], visited) for root in roots]
    )

    # TODO remove
    paths = []

    def handle_path(path: BFSPath[T]):
        if path.fully_visited:
            path.mark_visited()

    for path in open_path_queue:
        yield path
        handle_path(path)

    while open_path_queue:
        open_path = open_path_queue.popleft()

        for new_path in neighbours(open_path):
            neighbour = new_path.last
            # visited
            if neighbour in visited:
                continue
            # visited in path (loop)
            if neighbour in visited_partially and neighbour in open_path:
                continue

            visited_partially.add(neighbour)
            open_path_queue.append(new_path)

            # # TODO remove
            paths.append(new_path)
            if len(paths) % 50000 == 0:
                logger.info(f"{len(visited)} {len(visited_partially)} {len(paths)}")

            yield new_path
            handle_path(new_path)

    # TODO remove
    logger.info(f"Searched {len(paths)} paths")
