# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from typing import Callable, Self

from faebryk.library.has_placticity import has_placticity


class has_placticity_defined[T](has_placticity.impl()):
    def __init__(self, cost_function: Callable[[T], float], is_plastic = True) -> None:
        super().__init__()
        self.cost_function = cost_function
        self.is_plastic = is_plastic

    def get_cost_function(self) -> Callable[[T], float]:
        return self.cost_function

    def get_is_plastic(self) -> bool:
        return self.is_plastic

    def set_is_plastic(self, is_plastic: bool) -> Self:
        self.is_plastic = is_plastic
        return self
