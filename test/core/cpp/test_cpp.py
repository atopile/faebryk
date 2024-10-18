# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.cpp.graph import CGraph
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.test.times import Times

logger = logging.getLogger(__name__)


def test_graph_build():
    # python
    class App(Module):
        a: ModuleInterface
        b: ModuleInterface

        def __preinit__(self):
            self.a.connect(self.b)

    app = App()
    G = app.get_graph()

    # cpp
    Gpp = CGraph(G)

    assert Gpp.gif_py(Gpp._gif_c[app.a.self_gif]).node is app.a

    paths, _ = Gpp.find_paths(app.a, app.b)
    assert len(paths) == 2
    self_path, path = paths
    assert len(self_path.path) == 1
    assert self_path.path[0] is app.a.self_gif
    assert len(path.path) == 4
    assert path.path[0] is app.a.self_gif
    assert path.path[1] is app.a.connected
    assert path.path[2] is app.b.connected
    assert path.path[3] is app.b.self_gif


def test_graph_convert_performance():
    times = Times()

    app = F.USB2514B()
    G = app.get_graph()
    times.add("construct")

    CGraph(G)
    times.add("convert")

    logger.info(f"\n{times}")


if __name__ == "__main__":
    test_graph_build()
