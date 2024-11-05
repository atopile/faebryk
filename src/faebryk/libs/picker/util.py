# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.parameter import Parameter
from faebryk.library.Set import Set
from faebryk.libs.e_series import (
    E_SERIES,
    E_SERIES_VALUES,
    e_series_intersect,
)
from faebryk.libs.units import to_si_str
from faebryk.libs.util import cast_assert


def generate_si_values(
    value: Parameter, si_unit: str, e_series: E_SERIES | None = None
):
    """
    Generate a list of permissible SI values for the given parameter from an
    E-series
    """

    value = value.get_most_narrow()

    intersection = Set(
        [e_series_intersect(value, e_series or E_SERIES_VALUES.E_ALL)]
    ).params

    return [
        to_si_str(cast_assert(F.Constant, r).value, si_unit)
        .replace("µ", "u")
        .replace("inf", "∞")
        for r in intersection
    ]
