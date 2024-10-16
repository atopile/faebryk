# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import Any

import faebryk.library._F as F
import faebryk.libs.picker.api.picker_lib as P
from faebryk.core.core import Module
from faebryk.libs.picker.picker import PickError


class ApiPicker(F.has_multi_picker.FunctionPicker): ...


class StaticApiPartPicker(F.has_multi_picker.Picker):
    """
    Picks a specific part by ID or manufacturer / part number
    """

    # subject to change as the API evolves
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

    def pick(self, module: Module):
        match self.mfr, self.mfr_pn, self.lcsc_pn:
            case Any(mfr), Any(mfr_pn), None:
                parts = P.find_manufacturer_part(module, mfr, mfr_pn)
            case None, None, Any(lcsc_pn):
                parts = P.find_lcsc_part(module, lcsc_pn)
            case None, None, None:
                raise PickError("No parameters provided", module)

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


def add_api_pickers(module: Module, base_prio: int = 0) -> None:
    # Generic pickers
    F.has_multi_picker.add_to_module(
        module,
        base_prio,
        ApiPicker(P.find_lcsc_part),
    )
    F.has_multi_picker.add_to_module(
        module,
        base_prio,
        ApiPicker(P.find_manufacturer_part),
    )

    # Type-specific pickers
    F.has_multi_picker.add_pickers_by_type(
        module, P.TYPE_SPECIFIC_LOOKUP, ApiPicker, base_prio + 1
    )