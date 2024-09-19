# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import Collection

import dash_cytoscape as cyto
import rich
import rich.text
from dash import Dash, html

from faebryk.core.graphinterface import Graph, GraphInterface
from faebryk.core.link import Link
from faebryk.core.node import Node
from faebryk.exporters.visualize.util import generate_pastel_palette
from faebryk.libs.util import typename


# Transformers -------------------------------------------------------------------------
def _gif(gif: GraphInterface):
    return {
        "data": {
            "id": id(gif),
            "label": gif.get_full_name(),
            "type": type(gif).__name__,
            "parent": id(gif.node),
        }
    }


def _link(source, target, link: Link):
    return {
        "data": {
            "source": id(source),
            "target": id(target),
            "type": type(link).__name__,
        }
    }


def _group(node: Node):
    return {
        "data": {
            "id": id(node),
            "label": f"{node.get_full_name()} ({typename(node)})",
            "type": "group",
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
                "background-color": "#BFD7B5",
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
            },
        },
        {
            "selector": 'node[type = "group"]',
            "style": {
                "background-color": "#D3D3D3",
                "font-weight": "bold",
                "font-size": "1.5em",
                "text-valign": "top",
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


def interactive_graph(G: Graph):
    # Build elements
    edges = G.edges
    link_types = {typename(link) for _, _, link in edges}
    node_types = {typename(node) for node in G}

    elements = (
        [_gif(gif) for gif in G]
        + [_link(*edge) for edge in edges]
        + [_group(node) for node in G.node_projection()]
    )

    # Build stylesheet
    stylesheet = _Stylesheet()

    for node_type, color in _with_pastels(node_types):
        stylesheet.add_node_type(node_type, color)

    for link_type, color in _with_pastels(link_types):
        stylesheet.add_link_type(link_type, color)

    # Register the fcose layout
    cyto.load_extra_layouts()
    app = Dash(__name__)
    app.layout = _Layout(stylesheet, elements)

    # Print legend
    print("Node types:")
    for node_type, color in _with_pastels(node_types):
        colored_text = rich.text.Text(f"{node_type}: {color}")
        colored_text.stylize(f"on {color}")
        rich.print(colored_text)
    print("\n")

    print("Link types:")
    for link_type, color in _with_pastels(link_types):
        colored_text = rich.text.Text(f"{link_type}: {color}")
        colored_text.stylize(f"on {color}")
        rich.print(colored_text)
    print("\n")

    #
    app.run()
