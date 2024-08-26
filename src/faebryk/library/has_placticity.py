# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from abc import abstractmethod
from typing import Callable

from faebryk.core.parameter import Parameter
from faebryk.core.trait import Trait


class has_placticity[T](Trait):
    @abstractmethod
    def get_cost_function(self) -> Callable[[Parameter.LIT], float]: ...

    @abstractmethod
    def get_cost(self, value: Parameter.LIT) -> float: ...

    @abstractmethod
    def get_is_plastic(self) -> bool: ...

    @abstractmethod
    def set_is_plastic(self, is_plastic: bool) -> None: ...
