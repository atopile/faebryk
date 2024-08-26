# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

import faebryk.library._F as F


class has_kicad_footprint(F.Footprint.TraitT):
    @abstractmethod
    def get_kicad_footprint(self) -> str: ...

    @abstractmethod
    def get_pin_names(self) -> dict[F.Pad, str]: ...

    def get_kicad_footprint_name(self) -> str:
        return self.get_kicad_footprint().split(":")[-1]
