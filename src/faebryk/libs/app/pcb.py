# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.core import Module
from faebryk.core.util import get_node_tree, iter_tree_by_depth
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.exporters.pcb.routing.util import apply_route_in_pcb
from faebryk.library.has_pcb_layout import has_pcb_layout
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.has_pcb_position_defined import has_pcb_position_defined
from faebryk.library.has_pcb_routing_strategy import has_pcb_routing_strategy

logger = logging.getLogger(__name__)


def apply_layouts(app: Module):
    if not app.has_trait(has_pcb_position):
        app.add_trait(
            has_pcb_position_defined(
                has_pcb_position.Point((0, 0, 0, has_pcb_position.layer_type.NONE))
            )
        )

    tree = get_node_tree(app)
    for level in iter_tree_by_depth(tree):
        for n in level:
            if n.has_trait(has_pcb_layout):
                n.get_trait(has_pcb_layout).apply()


def apply_routing(app: Module, transformer: PCB_Transformer):
    # bottom up order

    tree = get_node_tree(app)
    for level in reversed(list(iter_tree_by_depth(tree))):
        for n in level:
            if n.has_trait(has_pcb_routing_strategy):
                routes = n.get_trait(has_pcb_routing_strategy).calculate(transformer)
                for route in routes:
                    apply_route_in_pcb(route, transformer)
