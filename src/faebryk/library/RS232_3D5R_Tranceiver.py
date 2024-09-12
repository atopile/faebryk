# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class RS232_3D5R_Tranceiver(Module):
    """
    Generic 3 drivers + 5 receivers RS232 Tranceiver base
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    uart: F.UART
    rs232: F.RS232

    # ----------------------------------------
    #                 traits
    # ----------------------------------------

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        pass
