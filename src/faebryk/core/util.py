# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import Iterable

from typing_extensions import deprecated

import faebryk.library._F as F
from faebryk.core.graphinterface import Graph, GraphInterfaceSelf
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.core.trait import Trait

logger = logging.getLogger(__name__)

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


# --------------------------------------------------------------------------------------


def use_interface_names_as_net_names(node: Node, name: str | None = None):
    if not name:
        p = node.get_parent()
        assert p
        name = p[1]

    name_prefix = node.get_full_name()

    el_ifs = node.get_children(types=F.Electrical, direct_only=False)

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
