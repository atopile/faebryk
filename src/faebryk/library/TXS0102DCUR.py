# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module






class TXS0102DCUR(Module):
    """
    TXS0102 2-Bit Bidirectional Voltage-Level Translator for
    Open-Drain and Push-Pull Applications
    """

    class _BidirectionalLevelShifter(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces

                io_a: F.ElectricLogic
                io_b: F.ElectricLogic

            # TODO: bridge shallow
    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.io_a, self.io_b)



        # interfaces

            voltage_a_power: F.ElectricPower
            voltage_b_power: F.ElectricPower
            n_oe: F.ElectricLogic


            shifters = L.if_list(2, self._BidirectionalLevelShifter)



        gnd = self.voltage_a_power.lv
        gnd.connect(self.voltage_b_power.lv)

        self.voltage_a_power.decoupled.decouple()
        self.voltage_b_power.decoupled.decouple()

        # eo is referenced to voltage_a_power (active high)
        self.n_oe.connect_reference(self.voltage_a_power)

        for shifter in self.shifters:
            side_a = shifter.io_a
            # side_a.reference.connect(self.voltage_a_power)
            side_a.add_trait(
                has_single_electric_reference_defined(self.voltage_a_power)
            )
            side_b = shifter.io_b
            # side_b.reference.connect(self.voltage_b_power)
            side_b.add_trait(
                has_single_electric_reference_defined(self.voltage_b_power)
            )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)("https://datasheet.lcsc.com/lcsc/1810292010_Texas-Instruments-TXS0102DCUR_C53434.pdf")
