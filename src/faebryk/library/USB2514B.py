# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, auto

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class USB2514B(Module):
    class InterfaceConfiguration(Enum):
        DEFAULT = auto()
        SMBUS = auto()
        BUS_POWERED = auto()
        EEPROM = auto()

    VDD33: F.ElectricPower
    VDDA33: F.ElectricPower

    PLLFILT: F.ElectricPower
    CRFILT: F.ElectricPower

    VBUS_DET: F.Electrical

    usb_downstream = L.if_list(4, F.DifferentialPair)
    usb_upstream = F.DifferentialPair

    XTALIN: F.Electrical
    XTALOUT: F.Electrical

    TEST: F.Electrical
    SUSP_IND: F.ElectricLogic
    RESET_N: F.Electrical
    RBIAS: F.Electrical
    NON_REM = L.if_list(2, F.ElectricLogic)
    LOCAL_PWR: F.Electrical
    CLKIN: F.Electrical
    CFG_SEL = L.if_list(2, F.ElectricLogic)

    HS_IND: F.ElectricLogic

    PRTPWR = L.if_list(4, F.ElectricLogic)
    PRT_DIS_P = L.if_list(4, F.ElectricLogic)
    PRT_DIS_M = L.if_list(4, F.ElectricLogic)
    OCS_N = L.if_list(4, F.ElectricLogic)
    BC_EN = L.if_list(4, F.ElectricLogic)

    i2c: F.I2C
    gnd: F.Electrical

    interface_configuration: F.TBD[InterfaceConfiguration]
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    def __preinit__(self):
        if self.interface_configuration == USB2514B.InterfaceConfiguration.DEFAULT:
            self.CFG_SEL[0].pulled.pull(up=False)
            self.CFG_SEL[1].pulled.pull(up=False)
        elif self.interface_configuration == USB2514B.InterfaceConfiguration.SMBUS:
            self.CFG_SEL[0].pulled.pull(up=True)
            self.CFG_SEL[1].pulled.pull(up=False)
        elif (
            self.interface_configuration == USB2514B.InterfaceConfiguration.BUS_POWERED
        ):
            self.CFG_SEL[0].pulled.pull(up=False)
            self.CFG_SEL[1].pulled.pull(up=True)
        elif self.interface_configuration == USB2514B.InterfaceConfiguration.EEPROM:
            self.CFG_SEL[0].pulled.pull(up=True)
            self.CFG_SEL[1].pulled.pull(up=True)

        # Add decoupling capacitors to power pins and connect all lv to gnd
        # TODO: decouple with 1.0uF and 0.1uF and maybe 4.7uF
        for g in self.get_children(direct_only=True, types=F.ElectricPower):
            g.decoupled.decouple()
            g.lv.connect(self.gnd)

        x = self

        x.CFG_SEL[0].connect(x.i2c.scl)
        x.CFG_SEL[1].connect(x.HS_IND)
        x.NON_REM[0].connect(x.SUSP_IND)
        x.NON_REM[1].connect(x.i2c.sda)

        x.RESET_N.connect(self.gnd)

    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/00001692C.pdf"
    )
