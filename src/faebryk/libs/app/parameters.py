# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.graphinterface import Graph
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.parameter import Parameter
from faebryk.libs.util import find

logger = logging.getLogger(__name__)


def replace_tbd_with_any(module: Module, recursive: bool, loglvl: int | None = None):
    """
    Replace all F.TBD instances with F.ANY instances in the given module.

    :param module: The module to replace F.TBD instances in.
    :param recursive: If True, replace F.TBD instances in submodules as well.
    """
    lvl = logger.getEffectiveLevel()
    if loglvl is not None:
        logger.setLevel(loglvl)

    module = module.get_most_special()

    for param in module.get_children(direct_only=True, types=Parameter):
        if isinstance(param.get_most_narrow(), F.TBD):
            logger.debug(f"Replacing in {module}: {param} with F.ANY")
            param.merge(F.ANY())

    logger.setLevel(lvl)

    if recursive:
        for m in module.get_children_modules(types=Module):
            replace_tbd_with_any(m, recursive=False, loglvl=loglvl)


# TODO this is an ugly hack until we have better params
def resolve_dynamic_parameters_alt(graph: Graph):
    params = [
        (param, trait)
        for param, trait in graph.nodes_with_trait(Parameter.is_dynamic)
        if isinstance(trait, F.is_dynamic_by_connections)
    ]

    mifs = {trait.mif_parent() for _, trait in params}
    print("MIFS", len(mifs))
    mifs_grouped: list[set[ModuleInterface]] = []
    while mifs:
        mif = mifs.pop()
        connections = {other for other in mifs if mif.is_connected_to(other)}
        connections.add(mif)
        mifs_grouped.append(connections)
        mifs.difference_update(connections)

    for _, trait in params:
        mif = trait.mif_parent()
        p_mifs = find(mifs_grouped, lambda mifs: mif in mifs)
        trait.exec_for_mifs(p_mifs)


def resolve_dynamic_parameters(graph: Graph):
    mifs: list[set[ModuleInterface]] = []

    params = [
        (param, trait)
        for param, trait in graph.nodes_with_trait(Parameter.is_dynamic)
        if isinstance(trait, F.is_dynamic_by_connections)
    ]

    mifs_ = {trait.mif_parent() for _, trait in params}
    while mifs_:
        mif = mifs_.pop()
        connections = set(mif.get_connected())
        mifs.append(connections)
        mifs_.difference_update(connections)

    for _, trait in params:
        mif = trait.mif_parent()
        p_mifs = find(mifs, lambda mifs: mif in mifs)
        trait.exec_for_mifs(p_mifs)
