# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_defined import has_designator_defined
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class Common_Mode_Filter(Module):
    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()): ...

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            c_a = L.if_list(2, Electrical)
            c_b = L.if_list(2, Electrical)

        self.IFs = _IFs(self)

        class _PARAMs(Module.PARAMS()): ...

        self.PARAMs = _PARAMs(self)

        self.add_trait(has_designator_defined("FL"))
