# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P
from faebryk.libs.util import times  # noqa: F401

logger = logging.getLogger(__name__)


class MultiCapacitor(F.Capacitor):
    """
    TODO: Docstring describing your module
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------

    # ----------------------------------------
    #                 traits
    # ----------------------------------------

    def __init__(self, count: int):
        self._count = count

    @L.rt_field
    def capacitors(self) -> list[F.Capacitor]:
        return times(self._count, F.Capacitor)

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        pass
