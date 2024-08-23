# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import Sequence


logger = logging.getLogger(__name__)


class has_footprint_requirement_defined(has_footprint_requirement.impl()):
    def __init__(self, req: Sequence[tuple[str, int]]) -> None:
        super().__init__()
        self.req = req

    def get_footprint_requirement(self) -> Sequence[tuple[str, int]]:
        return self.req
