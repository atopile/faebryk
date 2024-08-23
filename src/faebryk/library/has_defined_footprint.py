# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_defined_footprint(has_footprint_impl):
    def __init__(self, fp: F.Footprint) -> None:
        super().__init__()
        self.fp = fp

    def on_obj_set(self):
        self.set_footprint(self.fp)
