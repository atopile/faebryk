# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module, ModuleInterface


class RS485(ModuleInterface):
    diff_pair = DifferentialPair()
