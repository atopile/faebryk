# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.library.Electrical import Electrical
from faebryk.library.Footprint import Footprint


class can_attach_via_pinmap(Footprint.TraitT):
    @abstractmethod
    def attach(self, pinmap: dict[str, Electrical]): ...
