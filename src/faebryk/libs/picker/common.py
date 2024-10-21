# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.picker.picker import PickError


class StaticPartPicker(F.has_multi_picker.Picker, ABC):
    def __init__(
        self,
        *,
        mfr: str | None = None,
        mfr_pn: str | None = None,
        lcsc_pn: str | None = None,
    ) -> None:
        super().__init__()
        self.mfr = mfr
        self.mfr_pn = mfr_pn
        self.lcsc_pn = lcsc_pn

    def _friendly_description(self) -> str:
        desc = ""
        if self.mfr:
            desc += f"mfr={self.mfr}"
        if self.mfr_pn:
            desc += f"mfr_pn={self.mfr_pn}"
        if self.lcsc_pn:
            desc += f"lcsc_pn={self.lcsc_pn}"
        return desc or "<no params>"

    @abstractmethod
    def _find_parts(self, module: Module):
        pass

    def pick(self, module: Module):
        parts = self._find_parts(module)

        if len(parts) > 1:
            raise PickError(
                f"Multiple parts found for {self._friendly_description()}", module
            )

        if len(parts) < 1:
            raise PickError(
                f"Could not find part for {self._friendly_description()}", module
            )

        (part,) = parts
        try:
            part.attach(module, [])
        except ValueError as e:
            raise PickError(
                f"Could not attach part for {self._friendly_description()}", module
            ) from e
