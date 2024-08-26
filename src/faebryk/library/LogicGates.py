# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import TypeVar

import faebryk.library._F as F

T = TypeVar("T", bound=F.Logic)


class LogicGates:
    class OR(F.LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), F.LogicGate.can_logic_or_gate())

    class NOR(F.LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), F.LogicGate.can_logic_nor_gate())

    class NAND(F.LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(
                input_cnt, F.Constant(1), F.LogicGate.can_logic_nand_gate()
            )

    class XOR(F.LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), F.LogicGate.can_logic_xor_gate())
