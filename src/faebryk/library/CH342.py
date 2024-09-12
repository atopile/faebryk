# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, auto

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class CH342(Module):
    """
    Base class for CH342x USB to double UART converter
    """

    class DuplexMode(Enum):
        FULL = auto()
        HALF = auto()

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    usb: F.USB2_0
    uart = L.list_field(2, F.UART)
    tnow = L.list_field(2, F.ElectricLogic)
    ri = L.list_field(2, F.ElectricLogic)
    dcd = L.list_field(2, F.ElectricLogic)

    reset: F.ElectricLogic
    active: F.ElectricLogic

    vdd_5v: F.ElectricPower
    v_io: F.ElectricPower
    v_3v: F.ElectricPower

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wch-ic.com/downloads/CH342DS1_PDF.html"
    )

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self, gnd_only=True)
        )

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.vdd_5v.voltage.merge(F.Range(4 * P.V, 5.5 * P.V))
        self.v_3v.voltage.merge(F.Range.from_center(3.3 * P.V, 0.3 * P.V))
        self.v_io.voltage.merge(F.Range(1.7 * P.V, 5.5 * P.V))

        # ----------------------------------------
        #              connections
        # ----------------------------------------
