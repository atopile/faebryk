# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_single_electric_reference_defined(has_single_electric_reference.impl()):
    def __init__(self, reference: F.ElectricPower) -> None:
        super().__init__()
        self.reference = reference

    def get_reference(self) -> F.ElectricPower:
        return self.reference
