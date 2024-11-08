# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.cpp import Graph
from faebryk.core.graph import GraphFunctions
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.parameter import Parameter
from faebryk.libs.test.times import Times
from faebryk.libs.util import find, groupby

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


def resolve_dynamic_parameters(graph: Graph):
    mifs: list[set[ModuleInterface]] = []

    params = [
        (param, trait)
        for param, trait in GraphFunctions(graph).nodes_with_trait(Parameter.is_dynamic)
        if isinstance(trait, F.is_dynamic_by_connections)
    ]

    times = Times()
    mifs_ = groupby(params, lambda p: p[1].mif_parent())
    params_: set[tuple[Parameter, F.is_dynamic_by_connections]] = set()
    while mifs_:
        mif, mif_params = mifs_.popitem()
        connections = set(mif.get_connected())
        mifs.append(connections)

        for m in connections:
            if m in mifs_:
                del mifs_[m]
        params_.update(mif_params)

    times.add("get parameter connections")

    for _, trait in params_:
        mif = trait.mif_parent()
        p_mifs = find(mifs, lambda mifs: mif in mifs)
        trait.exec_for_mifs(p_mifs)

    times.add("merge parameters")
    logger.info(times)
