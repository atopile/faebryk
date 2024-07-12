# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from dataclasses import dataclass
from enum import IntEnum

from faebryk.core.core import Module, Node
from faebryk.core.util import get_all_nodes, get_parent_of_type
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.exporters.pcb.layout.layout import Layout
from faebryk.library.Electrical import Electrical
from faebryk.library.has_footprint import has_footprint
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.has_pcb_position_defined_relative_to_parent import (
    has_pcb_position_defined_relative_to_parent,
)
from faebryk.library.has_pcb_routing_strategy_greedy_direct_line import (
    has_pcb_routing_strategy_greedy_direct_line,
)
from faebryk.library.Pad import Pad
from faebryk.libs.kicad.fileformats import C_kicad_pcb_file
from faebryk.libs.util import NotNone, find, groupby

logger = logging.getLogger(__name__)


KFootprint = C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint
KPad = KFootprint.C_pad

# TODO move all those helpers and make them more general and precise


class Side(IntEnum):
    Right = 0
    Bottom = 90
    Left = 180
    Top = 270

    def rot(self, angle=90):
        return type(self)((self + angle) % 360)

    def rot_vector(self, vec: tuple[float, float]):
        x, y = vec
        if self == Side.Right:
            return x, y
        elif self == Side.Bottom:
            return -y, x
        elif self == Side.Left:
            return -x, -y
        elif self == Side.Top:
            return y, -x
        else:
            assert False


def _get_pad_side(fp: KFootprint, pad: KPad) -> Side:
    # TODO this def does not work well

    # relative to fp center
    if pad.at.x < 0 and abs(pad.at.x) > abs(pad.at.y):
        pos_side = Side.Left
    elif pad.at.x > 0 and abs(pad.at.x) > abs(pad.at.y):
        pos_side = Side.Right
    elif pad.at.y < 0 and abs(pad.at.y) > abs(pad.at.x):
        pos_side = Side.Top
    else:
        pos_side = Side.Bottom

    # pad size as heuristic
    rot = (fp.at.r - pad.at.r) % 360
    if pad.size.h > pad.size.w and rot not in (90, 270):
        pos_rot = {Side.Top, Side.Bottom}
    else:
        pos_rot = {Side.Right, Side.Left}

    if pos_side in pos_rot:
        return pos_side

    assert False


def _next_to_pad(
    fp: KFootprint, spad: KPad, dfp: KFootprint, dpad: KPad, distance: float
):
    def _add(v1, v2):
        return v1[0] + v2[0], v1[1] + v2[1]

    def _sub(v1, v2):
        return v1[0] - v2[0], v1[1] - v2[1]

    side = _get_pad_side(fp, spad)
    vec = side.rot_vector((distance, 0))
    vec = _add(vec, (spad.at.x, spad.at.y))

    def _rel_edge_of_pad(size):
        if side == Side.Top:
            return 0, 0 + size.h / 2
        elif side == Side.Bottom:
            return 0, 0 - size.h / 2
        elif side == Side.Left:
            return 0 - size.w / 2, 0
        else:
            return 0 + size.w / 2, 0

    vec = _add(vec, _rel_edge_of_pad(spad.size))
    vec = _add(vec, _rel_edge_of_pad(dpad.size))

    vec = _sub(vec, (dpad.at.x, dpad.at.y))

    return vec


def place_next_to_pad(module: Module, pad: Pad):
    kfp, kpad = pad.get_trait(PCB_Transformer.has_linked_kicad_pad).get_pad()

    nfp = module.get_trait(has_footprint).get_footprint()
    npad = find(
        {p for p in nfp.IFs.get_all() if isinstance(p, Pad)},
        lambda p: p.IFs.net.is_connected_to(pad.IFs.net) is not None,
    )
    nkfp, nkpad = npad.get_trait(PCB_Transformer.has_linked_kicad_pad).get_pad()

    # TODO rot & layer not correct
    pos = _next_to_pad(kfp, kpad, nkfp, nkpad, distance=1)

    module.add_trait(
        has_pcb_position_defined_relative_to_parent(
            (
                *pos,
                0,
                has_pcb_position.layer_type.NONE,
            )
        )
    )


def place_next_to(parent: Module, intf: Electrical, child: Module, route: bool = False):
    parent_fp = parent.get_trait(has_footprint).get_footprint()
    parent_pads = {p for p in parent_fp.IFs.get_all() if isinstance(p, Pad)}
    parent_pad = find(
        parent_pads, lambda p: p.IFs.net.is_connected_to(intf) is not None
    )

    place_next_to_pad(child, parent_pad)

    if route:
        intf.add_trait(
            has_pcb_routing_strategy_greedy_direct_line(extra_mifs=[parent_pad.IFs.net])
        )


@dataclass(frozen=True, eq=True)
class LayoutHeuristicElectricalClosenessDecouplingCaps(Layout):
    parent: Module

    def apply(self, *node: Node):
        from faebryk.library.Capacitor import Capacitor
        from faebryk.library.ElectricPower import ElectricPower

        # Remove nodes that have a position defined
        node = tuple(n for n in node if not n.has_trait(has_pcb_position))

        for n in node:
            assert isinstance(n, Capacitor)
            power = NotNone(get_parent_of_type(n, ElectricPower))

            hv = find(
                n.IFs.get_all(),
                lambda x: x.is_connected_to(power.IFs.hv) is not None
                and isinstance(x, Electrical),
            )
            assert isinstance(hv, Electrical)

            place_next_to(self.parent, hv, n, route=True)

    @staticmethod
    def find_module_candidates(node: Node):
        def _get_decoupling_caps():
            from faebryk.library.Capacitor import Capacitor
            from faebryk.library.ElectricPower import ElectricPower

            caps = {c for c in get_all_nodes(node) if isinstance(c, Capacitor)}
            for c in caps:
                power = get_parent_of_type(c, ElectricPower)
                if not power:
                    continue
                parent = get_parent_of_type(power, Module)
                if not parent:
                    continue

                yield parent, c

        return {
            k: [v[1] for v in v]
            for k, v in groupby(_get_decoupling_caps(), key=lambda x: x[0]).items()
        }

    @classmethod
    def add_to_all_suitable_modules(cls, node: Node):
        for parent, children in cls.find_module_candidates(node).items():
            layout = cls(parent)
            for c in children:
                c.add_trait(has_pcb_layout_defined(layout))
