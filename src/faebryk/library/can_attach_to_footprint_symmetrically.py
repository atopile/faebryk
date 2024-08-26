# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.util import zip_children_by_name


class can_attach_to_footprint_symmetrically(can_attach_to_footprint.impl()):
    def attach(self, footprint: F.Footprint):
        self.get_obj().add_trait(F.has_defined_footprint(footprint))

        for i, j in zip_children_by_name(footprint, self.get_obj(), ModuleInterface):
            assert isinstance(i, F.Pad)
            assert isinstance(j, F.Electrical)
            assert type(i.net) is type(j)
            i.attach(j)
