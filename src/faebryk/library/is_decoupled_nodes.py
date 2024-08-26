# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F

logger = logging.getLogger(__name__)


class is_decoupled_nodes(F.is_decoupled.impl()):
    def on_obj_set(self) -> None:
        assert hasattr(self.get_obj(), "capacitor")

    def get_capacitor(self) -> F.Capacitor:
        return self.get_obj().capacitor
