# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401
from faebryk.libs.util import NotNone

logger = logging.getLogger(__name__)


class CH342F_ReferenceDesign(Module):
    """
    Minimal reference implementation of the CH342F
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    ch324: F.CH342F

    def __init__(
        self,
        duplex_mode_uart_0: F.CH342.DuplexMode = F.CH342.DuplexMode.FULL,
        duplex_mode_uart_1: F.CH342.DuplexMode = F.CH342.DuplexMode.FULL,
    ) -> None:
        super().__init__()
        self._duplex_mode_uart_0 = duplex_mode_uart_0
        self._duplex_mode_uart_1 = duplex_mode_uart_1

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        # set the duplex mode
        if self._duplex_mode_uart_0 == F.CH342.DuplexMode.HALF:
            self.ch324.uart[0].dtr.get_trait(F.ElectricLogic.can_be_pulled).pull(
                up=False
            )
            NotNone(
                self.ch324.uart[0]
                .dtr.get_trait(F.ElectricLogic.has_pulls)
                .get_pulls()[1]
            ).resistance.merge(F.Constant(4.7 * P.kohm))
            self.ch324.tnow[0].connect(self.ch324.uart[0].dtr)
        if self._duplex_mode_uart_1 == F.CH342.DuplexMode.HALF:
            self.ch324.uart[1].dtr.get_trait(F.ElectricLogic.can_be_pulled).pull(
                up=False
            )
            NotNone(
                self.ch324.uart[1]
                .dtr.get_trait(F.ElectricLogic.has_pulls)
                .get_pulls()[1]
            ).resistance.merge(F.Constant(4.7 * P.kohm))
            self.ch324.tnow[1].connect(self.ch324.uart[1].dtr)

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        # configure for 3.3V GPIO operation with internal LDO
        self.ch324.vdd_5v.connect(self.ch324.usb.usb_if.buspower)
        self.ch324.v_3v.connect(self.ch324.v_io)

        self.ch324.vdd_5v.get_trait(F.can_be_decoupled).decouple()
        self.ch324.v_3v.get_trait(F.can_be_decoupled).decouple()
