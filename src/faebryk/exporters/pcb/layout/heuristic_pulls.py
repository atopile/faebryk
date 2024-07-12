# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from dataclasses import dataclass

from faebryk.core.core import Module, Node
from faebryk.core.util import get_all_nodes, get_parent_of_type
from faebryk.exporters.pcb.layout.heuristic_decoupling import place_next_to
from faebryk.exporters.pcb.layout.layout import Layout
from faebryk.library.Electrical import Electrical
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.libs.util import NotNone, find, groupby

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=True)
class LayoutHeuristicElectricalClosenessPullResistors(Layout):
    parent: Module

    def apply(self, *node: Node):
        from faebryk.library.ElectricLogic import ElectricLogic
        from faebryk.library.Resistor import Resistor

        # Remove nodes that have a position defined
        node = tuple(n for n in node if not n.has_trait(has_pcb_position))

        for n in node:
            assert isinstance(n, Resistor)
            logic = NotNone(get_parent_of_type(n, ElectricLogic))
            up, down = logic.get_trait(ElectricLogic.has_pulls).get_pulls()
            if n is up:
                level = logic.IFs.reference.IFs.hv
            elif n is down:
                level = logic.IFs.reference.IFs.lv
            else:
                assert False

            ic_side = find(
                n.IFs.get_all(),
                lambda intf: not intf.is_connected_to(level) is not None,
            )

            assert isinstance(ic_side, Electrical)

            place_next_to(self.parent, ic_side, n, route=True)

    @staticmethod
    def find_module_candidates(node: Node):
        def _get_modules():
            from faebryk.library.ElectricLogic import ElectricLogic
            from faebryk.library.Resistor import Resistor

            mods = {m for m in get_all_nodes(node) if isinstance(m, Resistor)}
            for m in mods:
                logic = get_parent_of_type(m, ElectricLogic)
                if not logic:
                    continue
                parent = get_parent_of_type(logic, Module)
                if not parent:
                    continue

                yield parent, m

        return {
            k: [v[1] for v in v]
            for k, v in groupby(_get_modules(), key=lambda x: x[0]).items()
        }

    @classmethod
    def add_to_all_suitable_modules(cls, node: Node):
        for parent, children in cls.find_module_candidates(node).items():
            layout = cls(parent)
            for c in children:
                c.add_trait(has_pcb_layout_defined(layout))
