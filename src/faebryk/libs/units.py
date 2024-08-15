# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

# re-exporting Quantity in-case we ever want to change it
from pint import Quantity, UnitRegistry  # noqa: F401
from pint.util import UnitsContainer  # noqa: F401


def to_si_str(
    value: Quantity,
    unit: str | UnitsContainer,
    num_decimals: int = 2,
) -> str:
    """
    Convert a float to a string with SI prefix and unit.
    """
    return f"{value.to_compact(unit):.{num_decimals}f~#P}"


P = UnitRegistry()
