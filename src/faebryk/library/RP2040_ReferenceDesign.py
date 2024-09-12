# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.picker.picker import DescriptiveProperties
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class RP2040_ReferenceDesign(Module):
    """Minimal required design for the Raspberry Pi RP2040 microcontroller.
    Based on the official Raspberry Pi RP2040 hardware design guidlines.
    """

    class Jumper(Module):
        logic_out: F.ElectricLogic

        resistor: F.Resistor
        switch = L.f_field(F.Switch(F.Electrical))()

        def __preinit__(self):
            self.resistor.resistance.merge(F.Range.from_center_rel(1 * P.kohm, 0.05))
            self.logic_out.set_weak(True).resistance.merge(self.resistor.resistance)
            self.logic_out.signal.connect_via(
                [self.resistor, self.switch], self.logic_out.reference.lv
            )

            self.switch.add(
                # TODO this is not nice
                F.has_footprint_defined(
                    F.KicadFootprint(
                        "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
                        pin_names=["1", "2"],
                    )
                )
            )

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------

    # function
    rp2040: F.RP2040
    ldo: F.LDO
    clock_source: F.Crystal_Oscillator
    flash: F.Winbond_Elec_W25Q128JVSIQ

    # IO
    usb: F.USB2_0

    # UI
    boot_selector: Jumper

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf"
    )

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        power_3v3 = F.ElectricPower()
        power_vbus = self.usb.usb_if.buspower

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        # LDO
        self.ldo.output_current.merge(F.Range.from_center_rel(600 * P.mA, 0.05))
        self.ldo.power_in.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(10 * P.uF, 0.05)
        )
        self.ldo.power_out.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(10 * P.uF, 0.05)
        )

        # XTAL
        self.clock_source.crystal.load_capacitance.merge(
            F.Range.from_center_rel(10 * P.pF, 0.05)
        )

        self.clock_source.current_limiting_resistor.resistance.merge(
            F.Range.from_center_rel(1 * P.kohm, 0.05)
        )
        self.clock_source.crystal.add(
            F.has_descriptive_properties_defined(
                {
                    DescriptiveProperties.manufacturer.value: "Abracon LLC",
                    DescriptiveProperties.partno: "ABM8-272-T3",
                }
            )
        )

        # USB
        terminated_usb = self.usb.usb_if.d.terminated()
        terminated_usb.impedance.merge(F.Range.from_center_rel(27.4 * P.ohm, 0.05))

        # Flash
        self.flash.memory_size.merge(16 * P.Mbit)
        self.flash.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(100 * P.nF, 0.05)
        )

        # Power rails
        self.rp2040.power_io.decoupled.decouple().specialize(
            F.MultiCapacitor(6)
        ).set_equal_capacitance_each(F.Range.from_center_rel(100 * P.nF, 0.05))
        self.rp2040.core_regulator.power_in.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(1 * P.uF, 0.05)
        )
        self.rp2040.power_adc.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(100 * P.nF, 0.05)
        )
        self.rp2040.power_usb_phy.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(100 * P.nF, 0.05)
        )
        power_3v3.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(10 * P.uF, 0.05)
        )
        self.rp2040.power_core.decoupled.decouple().specialize(
            F.MultiCapacitor(2)
        ).set_equal_capacitance_each(F.Range.from_center_rel(100 * P.nF, 0.05))
        self.rp2040.core_regulator.power_out.decoupled.decouple().capacitance.merge(
            F.Range.from_center_rel(1 * P.uF, 0.05)
        )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        # power
        power_vbus.connect_via(self.ldo, power_3v3)
        power_3v3.connect(
            self.rp2040.power_io,
            self.rp2040.power_adc,
            self.rp2040.power_usb_phy,
            self.flash.power,
        )
        power_3v3.connect_via(self.rp2040.core_regulator, self.rp2040.power_core)

        #
        self.flash.spi.connect(self.rp2040.qspi)
        self.flash.spi.cs.connect(self.boot_selector.logic_out)

        terminated_usb.connect(self.rp2040.usb)

        self.rp2040.xtal_if.connect(self.clock_source.xtal_if)

    @L.rt_field
    def pcb_layout(self):
        from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
        from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
        from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy

        Point = F.has_pcb_position.Point
        L = F.has_pcb_position.layer_type

        return F.has_pcb_layout_defined(
            layout=LayoutTypeHierarchy(
                layouts=[
                    LayoutTypeHierarchy.Level(
                        mod_type=F.RP2040,
                        layout=LayoutAbsolute(
                            Point((0, 0, 0, L.NONE)),
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=F.LDO,
                        layout=LayoutAbsolute(Point((0, 14, 0, L.NONE))),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=type(self.boot_selector),
                        layout=LayoutExtrude(
                            base=Point((-1.75, -11.5, 0, L.NONE)),
                            vector=(3.5, 0, 90),
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=type(self.flash),
                        layout=LayoutAbsolute(
                            Point((-1.95, -6.5, 0, L.NONE)),
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=F.Crystal_Oscillator,
                        layout=LayoutAbsolute(
                            Point((0, 7, 0, L.NONE)),
                        ),
                        children_layout=LayoutTypeHierarchy(
                            layouts=[
                                LayoutTypeHierarchy.Level(
                                    mod_type=F.Crystal,
                                    layout=LayoutAbsolute(
                                        Point((0, 0, 0, L.NONE)),
                                    ),
                                ),
                                LayoutTypeHierarchy.Level(
                                    mod_type=F.Capacitor,
                                    layout=LayoutExtrude(
                                        base=Point((-3, 0, 90, L.NONE)),
                                        vector=(0, 6, 180),
                                        dynamic_rotation=True,
                                    ),
                                ),
                            ]
                        ),
                    ),
                    LayoutTypeHierarchy.Level(
                        mod_type=F.Resistor,
                        layout=LayoutExtrude(
                            base=Point((0.75, -6, 0, L.NONE)),
                            vector=(1.25, 0, 270),
                        ),
                    ),
                ]
            )
        )
