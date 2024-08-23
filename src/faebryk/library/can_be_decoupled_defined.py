# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging


logger = logging.getLogger(__name__)


class can_be_decoupled_defined(can_be_decoupled.impl()):
    def __init__(self, hv: F.Electrical, lv: F.Electrical) -> None:
        super().__init__()
        self.hv = hv
        self.lv = lv

    def decouple(self):
        obj = self.get_obj()

        capacitor: F.Capacitor
        obj.add(capacitor, "capacitor")
        self.hv.connect_via(capacitor, self.lv)

        obj.add_trait(is_decoupled_nodes())
        return capacitor

    def is_implemented(self):
        return not self.get_obj().has_trait(is_decoupled)
