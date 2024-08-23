# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.core.module import Module


class can_attach_to_footprint(Module.TraitT):
    @abstractmethod
    def attach(self, footprint: F.Footprint): ...
