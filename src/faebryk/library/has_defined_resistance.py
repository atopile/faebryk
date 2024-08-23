# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.parameter import Parameter


class has_defined_resistance(has_resistance.impl()):
    def __init__(self, resistance: Parameter) -> None:
        super().__init__()
        self.component_resistance = resistance

    def get_resistance(self):
        return self.component_resistance
