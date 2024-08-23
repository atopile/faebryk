# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface


class Logic(ModuleInterface):
    @staticmethod
    def PARAMS():
        state = F.Range(False, True)

    def set(self, on: bool):
        self.state.merge(on)
