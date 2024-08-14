# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path

from faebryk.core.core import Trait


class has_origin_info(Trait):
    @dataclass
    class OriginInfo:
        file: Path
        line: int
        col: int

    @abstractmethod
    def get_origin(self) -> OriginInfo: ...
