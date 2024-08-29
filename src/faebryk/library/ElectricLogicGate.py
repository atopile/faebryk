# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import TypeVar

import faebryk.library._F as F
from faebryk.core.trait import TraitImpl
from faebryk.libs.library import L
from faebryk.libs.util import times

T = TypeVar("T", bound=F.Logic)


class ElectricLogicGate(F.LogicGate):
    def __init__(
        self,
        input_cnt: F.Constant[int],
        output_cnt: F.Constant[int],
        *functions: TraitImpl,
    ) -> None:
        self.input_cnt = input_cnt
        self.output_cnt = output_cnt
        super().__init__(input_cnt, output_cnt, *functions)

    def __preinit__(self):
        from faebryk.core.util import specialize_interface

        self_logic = self

        for in_if_l, in_if_el in zip(self_logic.inputs, self.inputs):
            specialize_interface(in_if_l, in_if_el)
        for out_if_l, out_if_el in zip(self_logic.outputs, self.outputs):
            specialize_interface(out_if_l, out_if_el)

    @L.rt_field
    def inputs(self):
        return times(self.input_cnt, F.ElectricLogic)

    @L.rt_field
    def outputs(self):
        return times(self.output_cnt, F.ElectricLogic)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )
