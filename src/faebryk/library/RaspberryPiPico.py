# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.exporters.pcb.layout.heuristic_decoupling import (
    LayoutHeuristicElectricalClosenessDecouplingCaps,
)
from faebryk.exporters.pcb.layout.heuristic_pulls import (
    LayoutHeuristicElectricalClosenessPullResistors,
)
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class RaspberryPiPico(Module):
    """
    Raspberry Pi Pico clone.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    base: F.RaspberryPiPicoBase_ReferenceDesign
    header = L.list_f_field(2, F.Header)(horizonal_pin_count=20, vertical_pin_count=1)
    usb_connector: F.USB_Type_C_Receptacle_16_pin
    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf"
    )

    @L.rt_field
    def designator_prefix(self):
        return F.has_designator_prefix_defined(F.has_designator_prefix.Prefix.MOD)

    @L.rt_field
    def pcb_layout(self):
        from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
        from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
        from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy

        Point = F.has_pcb_position.Point
        L = F.has_pcb_position.layer_type
        LVL = LayoutTypeHierarchy.Level

        layout = F.has_pcb_layout_defined(
            layout=LayoutTypeHierarchy(
                layouts=[
                    LVL(
                        mod_type=F.RaspberryPiPicoBase_ReferenceDesign,
                        layout=LayoutAbsolute(
                            Point((0, 0, 0, L.NONE)),
                        ),
                    ),
                    LVL(
                        mod_type=F.Header,
                        layout=LayoutExtrude(
                            base=Point((0, 0, L.NONE)), vector=(17.78, 0)
                        ),
                    ),
                    LVL(
                        mod_type=F.USB_Type_C_Receptacle_16_pin,
                        layout=LayoutAbsolute(
                            Point((17.78 / 2, 0, L.NONE)),
                        ),
                    ),
                ]
            )
        )

        LayoutHeuristicElectricalClosenessDecouplingCaps.add_to_all_suitable_modules(
            self
        )
        LayoutHeuristicElectricalClosenessPullResistors.add_to_all_suitable_modules(
            self
        )

        return layout

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        power_3v3 = self.base.ldo.power_out
        gnd = power_3v3.lv

        pin_count = 0
        for pin in self.header[0].contact:
            if pin in [2, 7, 12, 17]:
                pin.connect(gnd)
            else:
                pin.connect(self.base.rp2040.gpio[pin_count].signal)
                self.base.rp2040.pinmux.enable(self.base.rp2040.gpio[pin_count])
                pin_count += 1
        pin_count = 16
        for pin in self.header[1].contact:
            if pin in [2, 7, 12, 17]:
                pin.connect(gnd)
            elif pin == 9:
                pin.connect(self.base.rp2040.run.signal)
            elif pin == 14:
                ...  # TODO: ADC_VREF is not implemented
            elif pin == 15:
                pin.connect(power_3v3.hv)
            elif pin == 16:
                pin.connect(self.base.ldo.enable.signal)
            elif pin == 18:
                pin.connect(self.base.ldo.power_in.hv)
            elif pin == 19:
                pin.connect(self.base.usb.usb_if.buspower.hv)
            else:
                pin.connect(self.base.rp2040.gpio[pin_count].signal)
                self.base.rp2040.pinmux.enable(self.base.rp2040.gpio[pin_count])
                pin_count += 1

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        for header in self.header:
            header.pin_pitch.merge(2.54 * P.mm)
            header.mating_pin_lenght.merge(F.Range.from_center_rel(6 * P.mm, 0.1))
            header.pad_type.merge(F.Header.PadType.THROUGH_HOLE)
            header.pin_type.merge(F.Header.PinType.MALE)
            header.angle.merge(F.Header.Angle.STRAIGHT)
