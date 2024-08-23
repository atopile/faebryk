# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod


class can_switch_power(can_bridge):
    @abstractmethod
    def get_logic_in(self) -> F.ElectricLogic: ...
