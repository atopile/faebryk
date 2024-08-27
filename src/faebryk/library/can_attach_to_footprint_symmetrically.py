# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface


class can_attach_to_footprint_symmetrically(F.can_attach_to_footprint.impl()):
    def attach(self, footprint: F.Footprint):
        from faebryk.core.util import zip_children_by_name

        self.obj.add_trait(F.has_footprint_defined(footprint))

        for i, j in zip_children_by_name(footprint, self.obj, ModuleInterface):
            assert isinstance(i, F.Pad)
            assert isinstance(j, F.Electrical)
            assert type(i.net) is type(j)
            i.attach(j)
