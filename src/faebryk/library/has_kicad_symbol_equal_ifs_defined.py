# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_kicad_symbol_equal_ifs_defined(F.has_kicad_symbol.impl()):
    def __init__(self, symbol_name: str):
        super().__init__()
        self.symbol_name = symbol_name

    def get_pin_names(self):
        return self.obj.get_trait(F.has_equal_pins).get_pin_map()

    def get_kicad_symbol_name(self):
        return self.symbol_name
