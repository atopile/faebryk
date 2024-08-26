# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.parameter import Parameter


class has_defined_capacitance(F.has_capacitance.impl()):
    def __init__(self, capacitance: Parameter) -> None:
        super().__init__()
        self.component_capacitance = capacitance

    def get_capacitance(self):
        return self.component_capacitance
