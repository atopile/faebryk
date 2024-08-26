# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

import faebryk.library._F as F
from faebryk.core.module import Module


class has_footprint(Module.TraitT):
    @abstractmethod
    def get_footprint(self) -> F.Footprint: ...
