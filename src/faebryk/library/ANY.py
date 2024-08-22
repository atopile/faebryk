# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.parameter import Parameter


class ANY[PV](Parameter[PV]):
    """
    Allow parameter to take any value.
    Operations with this parameter automatically resolve to ANY too.
    Don't mistake with TBD.
    """

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, ANY):
            return True

        return False

    def __hash__(self) -> int:
        return super().__hash__()
