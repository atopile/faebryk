# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.cpp import faebryk_core_cpp as cpp
from faebryk.core.cpp.graph import CGraph
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface


def test_add():
    assert cpp.add(1, 2) == 3


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

    assert Gpp.gif_py(Gpp.gif_c[app.a.self_gif]).node is app.a

    paths = Gpp.find_paths(app.a, app.b)
    assert len(paths) == 1
    path = paths[0]
    assert len(path.gifs) == 4
    assert path.gifs[0] is app.a.self_gif
    assert path.gifs[1] is app.a.connected
    assert path.gifs[2] is app.b.connected
    assert path.gifs[3] is app.b.self_gif


if __name__ == "__main__":
    test_graph_build()
