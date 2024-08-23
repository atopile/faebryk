# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from enum import Enum, auto

from faebryk.core.parameter import Parameter


from faebryk.libs.units import Quantity


class LED(Diode):
    class Color(Enum):
        RED = auto()
        EMERALD = auto()
        GREEN = auto()
        BLUE = auto()
        YELLOW = auto()
        WHITE = auto()

        brightness: F.TBD[Quantity]
        max_brightness: F.TBD[Quantity]
        color: F.TBD[cls.Color]

        self.current.merge(self.brightness / self.max_brightness * self.max_current)

        self.inherit()

        # self.brightness.merge(
        #    F.Range(0 * P.millicandela, self.max_brightness)
        # )

    def set_intensity(self, intensity: Parameter[Quantity]) -> None:
        self.brightness.merge(intensity * self.max_brightness)

    def connect_via_current_limiting_resistor(
        self,
        input_voltage: Parameter[Quantity],
        resistor: F.Resistor,
        target: F.Electrical,
        low_side: bool,
    ):
        if low_side:
            self.cathode.connect_via(resistor, target)
        else:
            self.anode.connect_via(resistor, target)

        resistor.resistance.merge(
            self.get_needed_series_resistance_for_current_limit(input_voltage),
        )

    def connect_via_current_limiting_resistor_to_power(
        self, resistor: F.Resistor, power: F.ElectricPower, low_side: bool
    ):
        self.connect_via_current_limiting_resistor(
            power.voltage,
            resistor,
            power.lv if low_side else power.hv,
            low_side,
        )
