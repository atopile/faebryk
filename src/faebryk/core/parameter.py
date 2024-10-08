# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import math
from enum import Enum, auto
from typing import Protocol, runtime_checkable

from faebryk.core.core import Namespace
from faebryk.core.node import Node, f_field
from faebryk.libs.sets import Range, Set_
from faebryk.libs.units import P, Quantity, Unit

logger = logging.getLogger(__name__)


@runtime_checkable
class HasUnit(Protocol):
    unit: Unit


class ParameterOperatable(Protocol):
    type PE = ParameterOperatable | int | float | Quantity | Set_

    def alias_is(self, other: PE):
        pass

    def constrain_le(self, other: PE):
        pass

    def constrain_ge(self, other: PE):
        pass

    def constrain_lt(self, other: PE):
        pass

    def constrain_gt(self, other: PE):
        pass

    def constrain_ne(self, other: PE):
        pass

    def constrain_subset(self, other: PE):
        pass

    def constrain_superset(self, other: PE):
        pass

    def operation_add(self, other: PE) -> Expression:
        pass

    def operation_subtract(self, other: PE) -> Expression:
        pass

    def operation_multiply(self, other: PE) -> Expression:
        pass

    def operation_divide(self, other: PE) -> Expression:
        pass

    def operation_power(self, other: PE) -> Expression:
        pass

    def operation_log(self) -> Expression:
        pass

    def operation_sqrt(self) -> Expression:
        pass

    def operation_abs(self) -> Expression:
        pass

    def operation_floor(self) -> Expression:
        pass

    def operation_ceil(self) -> Expression:
        pass

    def operation_round(self) -> Expression:
        pass

    def operation_sin(self) -> Expression:
        pass

    def operation_cos(self) -> Expression:
        pass

    def operation_union(self, other: PE) -> Expression:
        pass

    def operation_intersection(self, other: PE) -> Expression:
        pass

    def operation_difference(self, other: PE) -> Expression:
        pass

    def operation_symmetric_difference(self, other: PE) -> Expression:
        pass

    def operation_and(self, other: PE) -> Expression:
        pass

    def operation_or(self, other: PE) -> Expression:
        pass

    def operation_not(self) -> Expression:
        pass

    def operation_xor(self, other: PE) -> Expression:
        pass

    def operation_implies(self, other: PE) -> Expression:
        pass

    # ----------------------------------------------------------------------------------
    def __add__(self, other: PE):
        return self.operation_add(other)

    def __sub__(self, other: PE):
        # TODO could be set difference
        return self.operation_subtract(other)

    def __mul__(self, other: PE):
        return self.operation_multiply(other)

    def __truediv__(self, other: PE):
        return self.operation_divide(other)

    def __rtruediv__(self, other: PE):
        return self.operation_divide(other)

    def __pow__(self, other: PE):
        return self.operation_power(other)

    def __abs__(self):
        return self.operation_abs()

    def __round__(self):
        return self.operation_round()

    def __and__(self, other: PE):
        # TODO could be set intersection
        return self.operation_and(other)

    def __or__(self, other: PE):
        # TODO could be set union
        return self.operation_or(other)

    def __xor__(self, other: PE):
        return self.operation_xor(other)


# TODO: prohibit instantiation
class Expression(Node, ParameterOperatable):
    pass


class Arithmetic(Expression):
    def __init__(self, *operands):
        types = [int, float, Quantity, Parameter, Arithmetic]
        if any(type(op) not in types for op in operands):
            raise ValueError(
                "operands must be int, float, Quantity, Parameter, or Expression"
            )
        if any(
            param.domain not in [Numbers, ESeries]
            for param in operands
            if isinstance(param, Parameter)
        ):
            raise ValueError("parameters must have domain Numbers or ESeries")
        self.operands = operands


class Additive(Arithmetic):
    def __init__(self, *operands):
        super().__init__(*operands)
        units = [
            op.unit if isinstance(op, HasUnit) else P.dimensionless for op in operands
        ]
        # Check if all units are compatible
        self.unit = units[0]
        if not all(u.is_compatible_with(self.unit) for u in units):
            raise ValueError("All operands must have compatible units")


class Add(Additive):
    def __init__(self, *operands):
        super().__init__(*operands)


class Subtract(Additive):
    def __init__(self, *operands):
        super().__init__(*operands)


class Multiply(Arithmetic):
    def __init__(self, *operands):
        super().__init__(*operands)
        self.unit = math.prod(
            [op.unit if isinstance(op, HasUnit) else P.dimensionless for op in operands]
        )


class Divide(Multiply):
    def __init__(self, numerator, denominator):
        super().__init__(numerator, denominator)
        self.unit = numerator.unit / denominator.unit


class Sqrt(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        self.unit = operand.unit**0.5


class Power(Arithmetic):
    def __init__(self, base, exponent: int):
        super().__init__(base, exponent)
        if isinstance(exponent, HasUnit) and not exponent.unit.is_compatible_with(
            P.dimensionless
        ):
            raise ValueError("exponent must have dimensionless unit")
        self.unit = (
            base.unit**exponent if isinstance(base, HasUnit) else P.dimensionless
        )


class Log(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        if not operand.unit.is_compatible_with(P.dimensionless):
            raise ValueError("operand must have dimensionless unit")
        self.unit = P.dimensionless


class Sin(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        if not operand.unit.is_compatible_with(P.dimensionless):
            raise ValueError("operand must have dimensionless unit")
        self.unit = P.dimensionless


class Cos(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        if not operand.unit.is_compatible_with(P.dimensionless):
            raise ValueError("operand must have dimensionless unit")
        self.unit = P.dimensionless


class Abs(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        self.unit = operand.unit


class Round(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        self.unit = operand.unit


class Floor(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        self.unit = operand.unit


class Ceil(Arithmetic):
    def __init__(self, operand):
        super().__init__(operand)
        self.unit = operand.unit


class Logic(Expression):
    pass


class And(Logic):
    pass


class Or(Logic):
    pass


class Not(Logic):
    pass


class Xor(Logic):
    pass


class Implies(Logic):
    pass


class Set(Expression):
    pass


class Union(Set):
    pass


class Intersection(Set):
    pass


class Difference(Set):
    pass


class SymmetricDifference(Set):
    pass


class Domain:
    pass


class ESeries(Domain):
    class SeriesType(Enum):
        E6 = auto()
        E12 = auto()
        E24 = auto()
        E48 = auto()
        E96 = auto()
        E192 = auto()

    def __init__(self, series: SeriesType):
        self.series = series


class Numbers(Domain):
    def __init__(
        self, *, negative: bool = True, zero_allowed: bool = True, integer: bool = False
    ) -> None:
        super().__init__()
        self.negative = negative
        self.zero_allowed = zero_allowed
        self.integer = integer


class Boolean(Domain):
    pass


class EnumDomain(Domain):
    def __init__(self, enum_t: type[Enum]):
        super().__init__()
        self.enum_t = enum_t


class Predicate(Node):
    pass


class LessThan(Predicate):
    pass


class GreaterThan(Predicate):
    pass


class LessOrEqual(Predicate):
    pass


class GreaterOrEqual(Predicate):
    pass


class NotEqual(Predicate):
    pass


class IsSubset(Predicate):
    pass


class IsSuperset(Predicate):
    pass


class Alias(Node):
    pass


class Is(Alias):
    pass


class Aliases(Namespace):
    IS = Is


# TODO rename?
class R(Namespace):
    """
    Namespace holding Expressions, Domains and Predicates for Parameters.
    R = paRameters
    """

    class Predicates(Namespace):
        class Element(Namespace):
            LT = LessThan
            GT = GreaterThan
            LE = LessOrEqual
            GE = GreaterOrEqual
            NE = NotEqual

        class Set(Namespace):
            IS_SUBSET = IsSubset
            IS_SUPERSET = IsSuperset

    class Domains(Namespace):
        class ESeries(Namespace):
            E6 = lambda: ESeries(ESeries.SeriesType.E6)  # noqa: E731
            E12 = lambda: ESeries(ESeries.SeriesType.E12)  # noqa: E731
            E24 = lambda: ESeries(ESeries.SeriesType.E24)  # noqa: E731
            E48 = lambda: ESeries(ESeries.SeriesType.E48)  # noqa: E731
            E96 = lambda: ESeries(ESeries.SeriesType.E96)  # noqa: E731
            E192 = lambda: ESeries(ESeries.SeriesType.E192)  # noqa: E731

        class Numbers(Namespace):
            REAL = Numbers
            NATURAL = lambda: Numbers(integer=True, negative=False)  # noqa: E731

        BOOL = Boolean
        ENUM = EnumDomain

    class Expressions(Namespace):
        class Arithmetic(Namespace):
            ADD = Add
            SUBTRACT = Subtract
            MULTIPLY = Multiply
            DIVIDE = Divide
            POWER = Power
            LOG = Log
            SQRT = Sqrt
            LOG = Log
            ABS = Abs
            FLOOR = Floor
            CEIL = Ceil
            ROUND = Round
            SIN = Sin
            COS = Cos

        class Logic(Namespace):
            AND = And
            OR = Or
            NOT = Not
            XOR = Xor
            IMPLIES = Implies

        class Set(Namespace):
            UNION = Union
            INTERSECTION = Intersection
            DIFFERENCE = Difference
            SYMMETRIC_DIFFERENCE = SymmetricDifference


class Parameter(Node, ParameterOperatable):
    def __init__(
        self,
        *,
        unit: Unit | Quantity | None = None,
        # hard constraints
        within: Range | None = None,
        domain: Domain = Numbers(negative=False),
        # soft constraints
        soft_set: Range | None = None,
        guess: Quantity
        | int
        | float
        | None = None,  # TODO actually allowed to be anything from domain
        tolerance_guess: Quantity | None = None,
        # hints
        likely_constrained: bool = False,
    ):
        super().__init__()
        if within is None:
            within = Range()
        if not within.is_compatible_with_unit(unit):
            raise ValueError("incompatible units")

        if not isinstance(unit, Unit):
            raise TypeError("unit must be a Unit")
        self.unit = unit
        self.within = within
        self.domain = domain
        self.soft_set = soft_set
        self.guess = guess
        self.tolerance_guess = tolerance_guess
        self.likely_constrained = likely_constrained

    # ----------------------------------------------------------------------------------
    type PE = ParameterOperatable.PE

    def alias_is(self, other: PE):
        pass

    def constrain_le(self, other: PE):
        pass

    def constrain_ge(self, other: PE):
        pass

    def constrain_lt(self, other: PE):
        pass

    def constrain_gt(self, other: PE):
        pass

    def constrain_ne(self, other: PE):
        pass

    def constrain_subset(self, other: PE):
        pass

    def operation_add(self, other: PE) -> Expression:
        pass

    def operation_subtract(self, other: PE) -> Expression:
        pass

    def operation_multiply(self, other: PE) -> Expression:
        pass

    def operation_divide(self, other: PE) -> Expression:
        pass

    def operation_power(self, other: PE) -> Expression:
        pass

    def operation_log(self) -> Expression:
        pass

    def operation_sqrt(self) -> Expression:
        pass

    def operation_abs(self) -> Expression:
        pass

    def operation_floor(self) -> Expression:
        pass

    def operation_ceil(self) -> Expression:
        pass

    def operation_round(self) -> Expression:
        pass

    def operation_sin(self) -> Expression:
        pass

    def operation_cos(self) -> Expression:
        pass

    def operation_union(self, other: PE) -> Expression:
        pass

    def operation_intersection(self, other: PE) -> Expression:
        pass

    def operation_difference(self, other: PE) -> Expression:
        pass

    def operation_symmetric_difference(self, other: PE) -> Expression:
        pass

    def operation_and(self, other: PE) -> Expression:
        pass

    def operation_or(self, other: PE) -> Expression:
        pass

    def operation_not(self) -> Expression:
        pass

    def operation_xor(self, other: PE) -> Expression:
        pass

    def operation_implies(self, other: PE) -> Expression:
        pass

    # ----------------------------------------------------------------------------------
    def __add__(self, other: PE):
        return self.operation_add(other)

    def __sub__(self, other: PE):
        # TODO could be set difference
        return self.operation_subtract(other)

    def __mul__(self, other: PE):
        return self.operation_multiply(other)

    def __truediv__(self, other: PE):
        return self.operation_divide(other)

    def __rtruediv__(self, other: PE):
        return self.operation_divide(other)

    def __pow__(self, other: PE):
        return self.operation_power(other)

    def __abs__(self):
        return self.operation_abs()

    def __round__(self):
        return self.operation_round()

    def __and__(self, other: PE):
        # TODO could be set intersection
        return self.operation_and(other)

    def __or__(self, other: PE):
        # TODO could be set union
        return self.operation_or(other)

    def __xor__(self, other: PE):
        return self.operation_xor(other)


p_field = f_field(Parameter)
