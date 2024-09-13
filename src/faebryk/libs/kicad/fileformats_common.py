import logging
import uuid
from dataclasses import dataclass, field
from enum import auto
from typing import Optional

from faebryk.libs.sexp.dataclass_sexp import SymEnum, sexp_field

logger = logging.getLogger(__name__)

# TODO find complete examples of the fileformats, maybe in the kicad repo


class UUID(str):
    pass


@dataclass
class C_xy:
    x: float = field(**sexp_field(positional=True))
    y: float = field(**sexp_field(positional=True))

    def __sub__(self, other: "C_xy") -> "C_xy":
        return C_xy(x=self.x - other.x, y=self.y - other.y)

    def __add__(self, other: "C_xy") -> "C_xy":
        return C_xy(x=self.x + other.x, y=self.y + other.y)

    def rotate(self, center: "C_xy", angle: float) -> "C_xy":
        import math

        angle = -angle  # rotate kicad style counter-clockwise

        # Translate point to origin
        translated_x = self.x - center.x
        translated_y = self.y - center.y

        # Convert angle to radians
        angle = math.radians(angle)

        # Rotate
        rotated_x = translated_x * math.cos(angle) - translated_y * math.sin(angle)
        rotated_y = translated_x * math.sin(angle) + translated_y * math.cos(angle)

        # Translate back
        new_x = rotated_x + center.x
        new_y = rotated_y + center.y

        return C_xy(x=new_x, y=new_y)


@dataclass
class C_xyz:
    x: float = field(**sexp_field(positional=True))
    y: float = field(**sexp_field(positional=True))
    z: float = field(**sexp_field(positional=True))


@dataclass
class C_xyr:
    x: float = field(**sexp_field(positional=True))
    y: float = field(**sexp_field(positional=True))
    r: float = field(**sexp_field(positional=True), default=0)


@dataclass
class C_wh:
    w: float = field(**sexp_field(positional=True))
    h: Optional[float] = field(**sexp_field(positional=True), default=None)


@dataclass
class C_stroke:
    class E_type(SymEnum):
        solid = auto()
        default = auto()

    width: float
    type: E_type


@dataclass
class C_effects:
    @dataclass
    class C_font:
        size: C_wh
        thickness: Optional[float] = None

    class E_justify(SymEnum):
        center = ""
        left = auto()
        right = auto()
        bottom = auto()
        top = auto()
        normal = ""
        mirror = auto()

    font: C_font
    justify: Optional[tuple[E_justify, E_justify, E_justify]] = None
    # TODO: this should be a Union as it's actually a tuple with 3 positional
    # and optional enums: (E_justify_horizontal, E_justify_vertical, E_mirrored)


@dataclass
class C_pts:
    xys: list[C_xy] = field(**sexp_field(multidict=True), default_factory=list)


def gen_uuid(mark: str = ""):
    # format: d864cebe-263c-4d3f-bbd6-bb51c6d2a608
    value = uuid.uuid4().hex

    suffix = mark.encode().hex()
    if suffix:
        value = value[: -len(suffix)] + suffix

    DASH_IDX = [8, 12, 16, 20]
    formatted = value
    for i, idx in enumerate(DASH_IDX):
        formatted = formatted[: idx + i] + "-" + formatted[idx + i :]

    return UUID(formatted)
