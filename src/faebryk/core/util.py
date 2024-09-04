# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum
from textwrap import indent
from typing import (
    Callable,
    Iterable,
    Sequence,
    cast,
)

from typing_extensions import deprecated

import faebryk.library._F as F
from faebryk.core.graphinterface import (
    Graph,
    GraphInterface,
    GraphInterfaceSelf,
)
from faebryk.core.link import Link, LinkDirect
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.core.parameter import Parameter
from faebryk.core.trait import Trait
from faebryk.libs.units import Quantity, UnitsContainer, to_si_str
from faebryk.libs.util import NotNone, Tree, cast_assert, zip_dicts_by_key, zip_exhaust

logger = logging.getLogger(__name__)

# Parameter ----------------------------------------------------------------------------


def enum_parameter_representation(param: Parameter, required: bool = False) -> str:
    if isinstance(param, F.Constant):
        return param.value.name if isinstance(param.value, Enum) else str(param.value)
    elif isinstance(param, F.Range):
        return (
            f"{enum_parameter_representation(param.min)} - "
            f"{enum_parameter_representation(param.max)}"
        )
    elif isinstance(param, F.Set):
        return f"Set({', '.join(map(enum_parameter_representation, param.params))})"
    elif isinstance(param, F.TBD):
        return "TBD" if required else ""
    elif isinstance(param, F.ANY):
        return "ANY" if required else ""
    else:
        return type(param).__name__


def as_unit(
    param: Parameter[Quantity],
    unit: str | UnitsContainer,
    base: int = 1000,
    required: bool = False,
) -> str:
    if base != 1000:
        raise NotImplementedError("Only base 1000 supported")
    if isinstance(param, F.Constant):
        return to_si_str(param.value, unit)
    elif isinstance(param, F.Range):
        return (
            as_unit(param.min, unit, base=base)
            + " - "
            + as_unit(param.max, unit, base=base, required=True)
        )
    elif isinstance(param, F.Set):
        return (
            "Set("
            + ", ".join(map(lambda x: as_unit(x, unit, required=True), param.params))
            + ")"
        )
    elif isinstance(param, F.TBD):
        return "TBD" if required else ""
    elif isinstance(param, F.ANY):
        return "ANY" if required else ""

    raise ValueError(f"Unsupported {param=}")


def as_unit_with_tolerance(
    param: Parameter, unit: str, base: int = 1000, required: bool = False
) -> str:
    if isinstance(param, F.Constant):
        return as_unit(param, unit, base=base)
    elif isinstance(param, F.Range):
        center, delta = param.as_center_tuple(relative=True)
        delta_percent_str = f"±{to_si_str(delta.value, "%", 0)}"
        return (
            f"{as_unit(center, unit, base=base, required=required)} {delta_percent_str}"
        )
    elif isinstance(param, F.Set):
        return (
            "Set("
            + ", ".join(
                map(lambda x: as_unit_with_tolerance(x, unit, base), param.params)
            )
            + ")"
        )
    elif isinstance(param, F.TBD):
        return "TBD" if required else ""
    elif isinstance(param, F.ANY):
        return "ANY" if required else ""
    raise ValueError(f"Unsupported {param=}")


def get_parameter_max(param: Parameter):
    if isinstance(param, F.Constant):
        return param.value
    if isinstance(param, F.Range):
        return param.max
    if isinstance(param, F.Set):
        return max(map(get_parameter_max, param.params))
    raise ValueError(f"Can't get max for {param}")


def with_same_unit(to_convert: float | int, param: Parameter | Quantity | float | int):
    if isinstance(param, F.Constant) and isinstance(param.value, Quantity):
        return Quantity(to_convert, param.value.units)
    if isinstance(param, Quantity):
        return Quantity(to_convert, param.units)
    if isinstance(param, (float, int)):
        return to_convert
    raise NotImplementedError(f"Unsupported {param=}")


# --------------------------------------------------------------------------------------

# Graph Querying -----------------------------------------------------------------------


# Make all kinds of graph filtering functions so we can optimize them in the future
# Avoid letting user query all graph nodes always because quickly very slow


def node_projected_graph(g: Graph) -> set[Node]:
    """
    Don't call this directly, use get_all_nodes_by/of/with instead
    """
    return Node.get_nodes_from_gifs(g.subgraph_type(GraphInterfaceSelf))


@deprecated("Use node_projected_graph or get_all_nodes_by/of/with")
def get_all_nodes_graph(g: Graph):
    return node_projected_graph(g)


def get_all_nodes_with_trait[T: Trait](
    g: Graph, trait: type[T]
) -> list[tuple[Node, T]]:
    return [
        (n, n.get_trait(trait)) for n in node_projected_graph(g) if n.has_trait(trait)
    ]


# Waiting for python to add support for type mapping
def get_all_nodes_with_traits[*Ts](
    g: Graph, traits: tuple[*Ts]
):  # -> list[tuple[Node, tuple[*Ts]]]:
    return [
        (n, tuple(n.get_trait(trait) for trait in traits))
        for n in node_projected_graph(g)
        if all(n.has_trait(trait) for trait in traits)
    ]


def get_all_nodes_by_names(g: Graph, names: Iterable[str]) -> list[tuple[Node, str]]:
    return [
        (n, node_name)
        for n in node_projected_graph(g)
        if (node_name := n.get_full_name()) in names
    ]


def get_all_nodes_of_type[T: Node](g: Graph, t: type[T]) -> set[T]:
    return {n for n in node_projected_graph(g) if isinstance(n, t)}


def get_all_nodes_of_types(g: Graph, t: tuple[type[Node], ...]) -> set[Node]:
    return {n for n in node_projected_graph(g) if isinstance(n, t)}


def get_direct_connected_nodes[T: Node](
    gif: GraphInterface, ty: type[T] = Node
) -> set[T]:
    out = Node.get_nodes_from_gifs(
        g for g, t in gif.edges.items() if isinstance(t, LinkDirect)
    )
    assert all(isinstance(n, ty) for n in out)
    return cast(set[T], out)


def get_mif_tree(
    obj: ModuleInterface | Module,
) -> dict[ModuleInterface, dict[ModuleInterface, dict]]:
    mifs = obj.get_children(direct_only=True, types=ModuleInterface)

    return {mif: get_mif_tree(mif) for mif in mifs}


def format_mif_tree(tree: dict[ModuleInterface, dict[ModuleInterface, dict]]) -> str:
    def str_tree(
        tree: dict[ModuleInterface, dict[ModuleInterface, dict]],
    ) -> dict[str, dict]:
        def get_name(k: ModuleInterface):
            # get_parent never none, since k gotten from parent
            return NotNone(k.get_parent())[1]

        return {
            f"{get_name(k)} ({type(k).__name__})": str_tree(v) for k, v in tree.items()
        }

    import json

    return json.dumps(str_tree(tree), indent=4)


# --------------------------------------------------------------------------------------


def use_interface_names_as_net_names(node: Node, name: str | None = None):
    if not name:
        p = node.get_parent()
        assert p
        name = p[1]

    name_prefix = node.get_full_name()

    el_ifs = {n for n in get_all_nodes(node) if isinstance(n, F.Electrical)}

    # for el_if in el_ifs:
    #    print(el_if)
    # print("=" * 80)

    # performance
    resolved: set[ModuleInterface] = set()

    # get representative interfaces that determine the name of the Net
    to_use: set[F.Electrical] = set()
    for el_if in el_ifs:
        # performance
        if el_if in resolved:
            continue

        connections = el_if.get_direct_connections() | {el_if}

        # skip ifs with Nets
        if matched_nets := {  # noqa: F841
            n
            for c in connections
            if (p := c.get_parent())
            and isinstance(n := p[0], F.Net)
            and n.part_of in connections
        }:
            # logger.warning(f"Skipped, attached to Net: {el_if}: {matched_nets!r}")
            resolved.update(connections)
            continue

        group = {mif for mif in connections if mif in el_ifs}

        # heuristic: choose shortest name
        picked = min(group, key=lambda x: len(x.get_full_name()))
        to_use.add(picked)

        # for _el_if in group:
        #    print(_el_if if _el_if is not picked else f"{_el_if} <-")
        # print("-" * 80)

        # performance
        resolved.update(group)

    nets: dict[str, tuple[F.Net, F.Electrical]] = {}
    for el_if in to_use:
        net_name = f"{name}{el_if.get_full_name().removeprefix(name_prefix)}"

        # name collision
        if net_name in nets:
            net, other_el = nets[net_name]
            raise Exception(
                f"{el_if} resolves to {net_name} but not connected"
                + f"\nwhile attaching nets to {node}={name} (connected via {other_el})"
                + "\n"
                + "\nConnections\n\t"
                + "\n\t".join(map(str, el_if.get_direct_connections()))
                + f"\n{'-'*80}"
                + "\nNet Connections\n\t"
                + "\n\t".join(map(str, net.part_of.get_direct_connections()))
            )

        net = F.Net()
        net.add(F.has_overriden_name_defined(net_name))
        net.part_of.connect(el_if)
        logger.debug(f"Created {net_name} for {el_if}")
        nets[net_name] = net, el_if


def with_names[N: Node](nodes: Iterable[N]) -> dict[str, N]:
    return {n.get_name(): n for n in nodes}
