# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface




class MultiSPI(ModuleInterface):
    def __init__(self, data_lane_count: int) -> None:
        super().__init__()


            clk: F.ElectricLogic
            data = L.if_list(data_lane_count, F.ElectricLogic)
            cs: F.ElectricLogic


