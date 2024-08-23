# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import TypeVar


T = TypeVar("T", bound=Logic)


class LogicGates:
    class OR(LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), LogicGate.can_logic_or_gate())

    class NOR(LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), LogicGate.can_logic_nor_gate())

    class NAND(LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), LogicGate.can_logic_nand_gate())

    class XOR(LogicGate):
        def __init__(self, input_cnt: F.Constant[int]):
            super().__init__(input_cnt, F.Constant(1), LogicGate.can_logic_xor_gate())
