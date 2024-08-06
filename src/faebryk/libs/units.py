# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.libs.util import round_str
from pint import UnitRegistry

# TODO remove and replace with P
E = 1e18
P_ = 1e15
T = 1e12
G = 1e9
M = 1e6
k = 1e3

d = 1e-1
c = 1e-2
m = 1e-3
u = 1e-6
n = 1e-9
p = 1e-12
f = 1e-15


si_prefixes = {
    "f": f,
    "p": p,
    "n": n,
    "µ": u,
    "m": m,
    "%": 1 / 100,
    "": 1,
    "k": k,
    "M": M,
    "G": G,
    "T": T,
    "P": P_,
    "E": E,
}


def si_str_to_float(si_value: str) -> float:
    """
    Convert a string with SI prefix and unit to a float.
    """

    prefix = ""
    value = si_value.replace("u", "µ")

    while value[-1].isalpha():
        prefix = value[-1]
        value = value[:-1]

    if prefix in si_prefixes:
        return float(value) * si_prefixes[prefix]

    return float(value)


def float_to_si_str(value: float, unit: str, num_decimals: int = 2) -> str:
    """
    Convert a float to a string with SI prefix and unit.
    """
    if value == float("inf"):
        return "∞" + unit
    elif value == float("-inf"):
        return "-∞" + unit

    res_factor = 1
    res_prefix = ""
    for prefix, factor in si_prefixes.items():
        if abs(value) >= factor:
            res_prefix = prefix
            res_factor = factor
        else:
            break

    value_str = round_str(value / res_factor, num_decimals)

    return value_str + res_prefix + unit


P = UnitRegistry()
