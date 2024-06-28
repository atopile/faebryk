# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.core.core import NodeTrait


class has_construction_dependency(NodeTrait):
    def __init__(self) -> None:
        super().__init__()
        self.executed = False

    @abstractmethod
    def construct(self): ...

    def _fullfill(self):
        self.executed = True

    def is_implemented(self):
        return not self.executed
