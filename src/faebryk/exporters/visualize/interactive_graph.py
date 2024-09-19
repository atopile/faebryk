# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import Collection, Iterable

import dash_cytoscape as cyto
import rich
import rich.text
from dash import Dash, html

import faebryk.library._F as F
from faebryk.core.graphinterface import Graph, GraphInterface
from faebryk.core.link import Link
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.core.parameter import Parameter
from faebryk.core.trait import Trait
from faebryk.exporters.visualize.util import generate_pastel_palette
from faebryk.libs.util import KeyErrorAmbiguous, find_or, typename


# Transformers -------------------------------------------------------------------------
def _gif(gif: GraphInterface):
    return {
        "data": {
            "id": id(gif),
            "label": gif.name,
            "type": typename(gif),
            "parent": id(gif.node),
        }
    }


def _link(source, target, link: Link):
    return {
        "data": {
            "source": id(source),
            "target": id(target),
            "type": typename(link),
        }
    }


_GROUP_TYPES = {
    Parameter: "#FFD9DE",  # Very light pink
    Module: "#E0F0FF",  # Very light blue
    Trait: "#FCFCFF",  # Almost white
    F.Electrical: "#D1F2EB",  # Very soft turquoise
    F.ElectricPower: "#FCF3CF",  # Very light goldenrod
    F.ElectricLogic: "#EBE1F1",  # Very soft lavender
    # Defaults
    ModuleInterface: "#DFFFE4",  # Very light green
    Node: "#FCFCFF",  # Almost white
}


def _group(node: Node):
    try:
        subtype = find_or(_GROUP_TYPES, lambda t: isinstance(node, t), default=Node)
    except KeyErrorAmbiguous as e:
        subtype = e.duplicates[0]

    return {
        "data": {
            "id": id(node),
            "label": f"{node.get_full_name()}\n({typename(node)})",
            "type": "group",
            "subtype": typename(subtype),
        }
    }


# Style --------------------------------------------------------------------------------


def _with_pastels[T](iterable: Collection[T]):
    return zip(iterable, generate_pastel_palette(len(iterable)))


class _Stylesheet:
    _BASE = [
        {
            "selector": "node",
            "style": {
                "content": "data(label)",
                "text-opacity": 0.8,
                "text-valign": "center",
                "text-halign": "center",
                "font-size": "0.5em",
                "background-color": "#BFD7B5",
                "text-outline-color": "#FFFFFF",
                "text-outline-width": 0.5,
                "border-width": 1,
                "border-color": "#888888",
                "border-opacity": 0.5,
            },
        },
        {
            "selector": "edge",
            "style": {
                "width": 1,
                "line-color": "#A3C4BC",
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "arrow-scale": 1,
                "target-arrow-color": "#A3C4BC",
                "text-outline-color": "#FFFFFF",
                "text-outline-width": 2,
            },
        },
        {
            "selector": 'node[type = "group"]',
            "style": {
                "background-color": "#D3D3D3",
                "font-weight": "bold",
                "font-size": "1.5em",
                "text-valign": "top",
                "text-outline-color": "#FFFFFF",
                "text-outline-width": 1.5,
                "text-wrap": "wrap",
            },
        },
    ]

    def __init__(self):
        self.stylesheet = list(self._BASE)

    def add_node_type(self, node_type: str, color: str):
        self.stylesheet.append(
            {
                "selector": f'node[type = "{node_type}"]',
                "style": {"background-color": color},
            }
        )

    def add_link_type(self, link_type: str, color: str):
        self.stylesheet.append(
            {
                "selector": f'edge[type = "{link_type}"]',
                "style": {"line-color": color, "target-arrow-color": color},
            }
        )

    def add_group_type(self, group_type: str, color: str):
        self.stylesheet.append(
            {
                "selector": f'node[subtype = "{group_type}"]',
                "style": {"background-color": color},
            }
        )


def _Layout(stylesheet: _Stylesheet, elements: list[dict[str, dict]]):
    return html.Div(
        style={
            "position": "fixed",
            "display": "flex",
            "flex-direction": "column",
            "height": "100%",
            "width": "100%",
        },
        children=[
            html.Div(
                className="cy-container",
                style={"flex": "1", "position": "relative"},
                children=[
                    cyto.Cytoscape(
                        id="graph-view",
                        stylesheet=stylesheet.stylesheet,
                        style={
                            "position": "absolute",
                            "width": "100%",
                            "height": "100%",
                            "zIndex": 999,
                        },
                        elements=elements,
                        layout={
                            "name": "fcose",
                            "quality": "proof",
                            "animate": False,
                            "randomize": False,
                            "fit": True,
                            "padding": 50,
                            "nodeDimensionsIncludeLabels": True,
                            "uniformNodeDimensions": False,
                            "packComponents": True,
                            "nodeRepulsion": 8000,
                            "idealEdgeLength": 50,
                            "edgeElasticity": 0.45,
                            "nestingFactor": 0.1,
                            "gravity": 0.25,
                            "numIter": 2500,
                            "tile": True,
                            "tilingPaddingVertical": 10,
                            "tilingPaddingHorizontal": 10,
                            "gravityRangeCompound": 1.5,
                            "gravityCompound": 1.0,
                            "gravityRange": 3.8,
                            "initialEnergyOnIncremental": 0.5,
                        },
                    )
                ],
            ),
        ],
    )


# --------------------------------------------------------------------------------------


def interactive_subgraph(
    edges: Iterable[tuple[GraphInterface, GraphInterface, Link]],
    gifs: list[GraphInterface],
    nodes: Iterable[Node],
):
    links = [link for _, _, link in edges]
    link_types = {typename(link) for link in links}
    gif_types = {typename(gif) for gif in gifs}

    elements = (
        [_gif(gif) for gif in gifs]
        + [_link(*edge) for edge in edges]
        + [_group(node) for node in nodes]
    )

    # Build stylesheet
    stylesheet = _Stylesheet()

    gif_type_colors = list(_with_pastels(gif_types))
    link_type_colors = list(_with_pastels(link_types))
    group_types_colors = [
        (typename(group_type), color) for group_type, color in _GROUP_TYPES.items()
    ]

    for gif_type, color in gif_type_colors:
        stylesheet.add_node_type(gif_type, color)

    for link_type, color in link_type_colors:
        stylesheet.add_link_type(link_type, color)

    for group_type, color in group_types_colors:
        stylesheet.add_group_type(group_type, color)

    # Register the fcose layout
    cyto.load_extra_layouts()
    app = Dash(__name__)
    app.layout = _Layout(stylesheet, elements)

    # Print legend
    def legend_block(text: str, color: str):
        colored_blocks = rich.text.Text(" " * 5)
        colored_blocks.style = f"on {color}"
        rich.print(colored_blocks, text)

    for typegroup, colors in [
        ("Node", gif_type_colors),
        ("Link", link_type_colors),
        ("Group", group_types_colors),
    ]:
        print(f"{typegroup} types:")
        for text, color in colors:
            legend_block(text, color)
        print("\n")

    #
    app.run(jupyter_height=1800)


def interactive_graph(G: Graph, node_types: tuple[type[Node], ...] | None = None):
    if node_types is None:
        node_types = (Node,)

    # Build elements
    nodes = G.nodes_of_types(node_types)
    gifs = [gif for gif in G if gif.node in nodes]
    edges = [
        (edge[0], edge[1], edge[2])
        for edge in G.edges
        if edge[0] in gifs and edge[1] in gifs
    ]
    return interactive_subgraph(edges, gifs, nodes)
