# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from math import inf
from typing import Any, Protocol, Self, TypeVar

from faebryk.core.core import Parameter
from faebryk.library.Constant import Constant

X = TypeVar("X", bound="_SupportsRangeOps")


class _SupportsRangeOps(Protocol):
    def __add__(self, __value: X) -> X: ...

    def __sub__(self, __value: X) -> X: ...

    def __mul__(self, __value: X) -> X: ...

    def __le__(self, __value: X) -> bool: ...

    def __lt__(self, __value: X) -> bool: ...

    def __ge__(self, __value: X) -> bool: ...


class Range[PV: _SupportsRangeOps](Parameter[PV]):
    def __init__(self, *bounds: PV | Parameter[PV]) -> None:
        super().__init__()

        # TODO this should not be here, but be dynamically resolved during comparison
        # if isinstance(bound1, Range):
        #    bound1 = bound1.min

        # if isinstance(bound2, Range):
        #    bound2 = bound2.max

        self.bounds: list[Parameter[PV]] = [
            bound if isinstance(bound, Parameter) else Constant(bound)
            for bound in bounds
        ]

    def _get_narrowed_bounds(self) -> list[Parameter[PV]]:
        return list({b.get_most_narrow() for b in self.bounds})

    @property
    def min(self) -> Parameter[PV]:
        return min(self._get_narrowed_bounds())

    @property
    def max(self) -> Parameter[PV]:
        return max(self._get_narrowed_bounds())

    def contains(self, value_to_check: PV) -> bool:
        return self.min <= value_to_check and self.max >= value_to_check

    def as_tuple(self) -> tuple[Parameter[PV], Parameter[PV]]:
        return (self.min, self.max)

    def as_center_tuple(self) -> tuple[Parameter[PV], Parameter[PV]]:
        return (self.min + self.max) / 2, (self.max - self.min) / 2

    @classmethod
    def from_center(
        cls, center: PV | Parameter[PV], delta: PV | Parameter[PV]
    ) -> "Range[PV]":
        return cls(center - delta, center + delta)

    @classmethod
    def from_center_rel(cls, center: PV, factor: PV) -> "Range[PV]":
        return cls.from_center(center, center * factor)

    @classmethod
    def lower_bound(cls, lower: PV) -> "Range[PV]":
        # TODO range should take params as bounds
        return cls(lower, inf)

    @classmethod
    def upper_bound(cls, upper: PV) -> "Range[PV]":
        # TODO range should take params as bounds
        return cls(0, upper)

    def __str__(self) -> str:
        bounds = map(str, self._get_narrowed_bounds())
        return super().__str__() + f"({', '.join(bounds)})"

    def __repr__(self):
        bounds = map(repr, self._get_narrowed_bounds())
        return super().__repr__() + f"({', '.join(bounds)})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Range):
            return False
        return set(self.bounds) == set(other.bounds)

    def __hash__(self) -> int:
        return sum(hash(b) for b in self.bounds)

    # comparison operators
    def __le__(self, other) -> bool:
        return self.max <= other

    def __lt__(self, other) -> bool:
        return self.max < other

    def __ge__(self, other) -> bool:
        return self.min >= other

    def __gt__(self, other) -> bool:
        return self.min > other

    def __format__(self, format_spec):
        bounds = [format(b, format_spec) for b in self._get_narrowed_bounds()]
        return f"{super().__str__()}({', '.join(bounds)})"

    def copy(self) -> Self:
        return type(self)(*self.bounds)

    def conjunct[T: Parameter](self, other: T) -> T:
        from faebryk.library.Set import Set

        if isinstance(other, Set):
            return Set(s for s in other.params if self.contains(s))

        raise NotImplementedError()

    def __and__[T: Parameter](self, other: T) -> T:
        return self.conjunct(other)
