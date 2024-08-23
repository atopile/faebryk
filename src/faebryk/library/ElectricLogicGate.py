# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import TypeVar

import faebryk.library._F as F
from faebryk.core.trait import TraitImpl
from faebryk.core.util import specialize_interface
from faebryk.libs.library import L

T = TypeVar("T", bound=F.Logic)


class ElectricLogicGate(F.LogicGate):
    inputs = L.if_list(0, F.ElectricLogic)
    outputs = L.if_list(0, F.ElectricLogic)

    def __init__(
        self,
        input_cnt: F.Constant[int],
        output_cnt: F.Constant[int],
        *functions: TraitImpl,
    ) -> None:
        super().__init__(input_cnt, output_cnt, *functions)

        self.add_to_container(int(input_cnt), F.ElectricLogic, self.inputs)
        self.add_to_container(int(output_cnt), F.ElectricLogic, self.outputs)

        self_logic = self

        for in_if_l, in_if_el in zip(self_logic.inputs, self.inputs):
            specialize_interface(in_if_l, in_if_el)
        for out_if_l, out_if_el in zip(self_logic.outputs, self.outputs):
            specialize_interface(out_if_l, out_if_el)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )
