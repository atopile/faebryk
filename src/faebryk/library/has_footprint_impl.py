# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.link import LinkNamedParent


class has_footprint_impl(F.has_footprint.impl()):
    def set_footprint(self, fp: F.Footprint):
        self.obj.children.connect(fp.parent, LinkNamedParent.curry("footprint"))

    def get_footprint(self) -> F.Footprint:
        children = self.obj.children.get_children()
        fps = [c for _, c in children if isinstance(c, F.Footprint)]
        assert len(fps) == 1, f"candidates: {fps}"
        return fps[0]
