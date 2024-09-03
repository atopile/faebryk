# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.core.trait import Trait


class has_construction_dependency(Trait):
    def __preinit__(self) -> None:
        self.executed = False

    @abstractmethod
    def construct(self): ...

    def _fullfill(self):
        self.executed = True

    def is_implemented(self):
        return not self.executed
