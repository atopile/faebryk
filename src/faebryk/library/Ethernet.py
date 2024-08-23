# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module, ModuleInterface


class Ethernet(ModuleInterface):
    tx = DifferentialPair()
    rx = DifferentialPair()
