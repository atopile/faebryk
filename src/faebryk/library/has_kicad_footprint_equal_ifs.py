# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_kicad_footprint_equal_ifs(has_kicad_footprint.impl()):
    def get_pin_names(self):
        return self.get_obj().get_trait(has_equal_pins).get_pin_map()
