# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

# re-exporting Quantity in-case we ever want to change it
from typing import Any

from pint import Quantity as _Quantity  # noqa: F401
from pint import UndefinedUnitError, Unit, UnitRegistry  # noqa: F401
from pint.util import UnitsContainer as _UnitsContainer

from faebryk.libs.util import cast_assert

P = UnitRegistry()

UnitsContainer = _UnitsContainer | str
Quantity = P.Quantity
dimensionless = cast_assert(Unit, P.dimensionless)


class HasUnit:
    units: Unit

    @staticmethod
    def check(obj: Any) -> bool:
        return hasattr(obj, "units")

    @staticmethod
    def get_units_or_dimensionless(obj: Any) -> Unit:
        return obj.units if HasUnit.check(obj) else dimensionless


def to_si_str(
    value: Quantity | float | int,
    unit: UnitsContainer,
    num_decimals: int = 2,
) -> str:
    """
    Convert a float to a string with SI prefix and unit.
    """
    from faebryk.libs.util import round_str

    if isinstance(value, Quantity):
        out = f"{value.to(unit).to_compact(unit):.{num_decimals}f~#P}"
    else:
        out = f"{round_str(value, num_decimals)} {unit}"
    m, u = out.split(" ")
    if "." in m:
        int_, frac = m.split(".")
        clean_decimals = frac.rstrip("0")
        m = f"{int_}.{clean_decimals}" if clean_decimals else int_

    return f"{m}{u}"


def Scalar(value: float):
    return Quantity(value)
