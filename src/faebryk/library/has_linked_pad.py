# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface


class has_linked_pad(ModuleInterface.TraitT):
    @abstractmethod
    def get_pad(self) -> F.Pad: ...
