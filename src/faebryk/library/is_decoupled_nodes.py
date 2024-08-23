# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging


logger = logging.getLogger(__name__)


class is_decoupled_nodes(is_decoupled.impl()):
    def on_obj_set(self) -> None:
        assert hasattr(self.get_obj(), "capacitor")

    def get_capacitor(self) -> F.Capacitor:
        return self.get_obj().capacitor
