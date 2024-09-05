# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class RS232_3D5R_Tranceiver(F.RS232TranceiverBase):
    """
    Generic 3 drivers + 5 receivers RS232 Tranceiver
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    uart_logic = F.UART
    uart_rs232 = F.RS232

    enable: F.ElectricLogic
    online: F.ElectricLogic
    status: F.ElectricLogic

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
