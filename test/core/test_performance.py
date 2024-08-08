# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import time
import unittest
from itertools import pairwise
from textwrap import indent
from typing import Callable

import faebryk.core.util as core_util
import faebryk.library._F as F
from faebryk.core.core import GraphInterface, Module
from faebryk.libs.util import times


class Times:
    def __init__(self) -> None:
        self.times = {}
        self.last_time = time.time()

    def add(self, name: str):
        now = time.time()
        if name not in self.times:
            self.times[name] = now - self.last_time
        self.last_time = now

    def _format_val(self, val: float):
        return f"{val * 1000:.2f}ms"

    def __repr__(self):
        formatted = {k: self._format_val(v) for k, v in self.times.items()}
        return "Timings: \n" + indent(
            "\n".join(f"{k.rjust(20)}: {v.rjust(10)}" for k, v in formatted.items()),
            " " * 4,
        )


class TestPerformance(unittest.TestCase):
    # TODO re-enable
    # @unittest.skip("")
    def test_get_all(self):
        def _factory_simple_resistors(count: int):
            class App(Module):
                def __init__(self) -> None:
                    super().__init__()

                    class NODES(super().NODES()):
                        resistors = times(count, F.Resistor)

                    self.NODEs = NODES(self)

            return App

        def _common_timings(factory: Callable[[], type[Module]], test_name: str):
            timings = Times()

            App = factory()
            timings.add("classdef")

            app = App()
            timings.add("instance")

            G = app.get_graph()
            timings.add("graph")

            core_util.get_all_nodes(app)
            timings.add("get_all_nodes")

            core_util.get_all_nodes_graph(G())
            timings.add("get_all_nodes_graph")

            core_util.get_node_tree(app)
            timings.add("get_node_tree")

            core_util.get_mif_tree(app)
            timings.add("get_mif_tree")

            print(test_name.ljust(60, "-"))
            print(f"{timings!r}")
            print(str(G))
            return timings

        _common_timings(lambda: _factory_simple_resistors(1), "Simple resistors: 1")

        for i in range(7):
            count = 10 * 2**i
            timings = _common_timings(
                lambda: _factory_simple_resistors(count), f"Simple resistors: {count}"
            )
            per_resistor = timings.times["instance"] / count
            print(f"----> Avg/resistor: {per_resistor*1e3:.2f} ms")

    @unittest.skip("")
    def test_graph_merge_rec(self):
        timings = Times()
        count = 2**14

        gs = times(count, GraphInterface)
        timings.add("instance")

        def rec_connect(gs_sub: list[GraphInterface]):
            if len(gs_sub) == 1:
                return gs_sub[0]

            mid = len(gs_sub) // 2

            now = time.time()
            timings.add(f"recurse {len(gs_sub)}")
            left = rec_connect(gs_sub[:mid])
            right = rec_connect(gs_sub[mid:])
            timings.times[f"split {len(gs_sub)}"] = time.time() - now

            timings.add(f"connect {len(gs_sub)}")
            left.connect(right)

            return left

        now = time.time()
        rec_connect(gs)
        timings.times["connect"] = time.time() - now
        per_connect = timings.times["connect"] / count

        self.assertLess(per_connect, 80e-6)
        self.assertLess(timings.times["connect 2"], 20e-6)
        # self.assertLess(timings.times["connect 1024"], 3e-3)
        # self.assertLess(timings.times["split 1024"], 50e-3)
        self.assertLess(timings.times["instance"], 300e-3)
        self.assertLess(timings.times["connect"], 1200e-3)
        print(timings)
        print(f"----> Avg/connect: {per_connect*1e6:.2f} us")

    @unittest.skip("")
    def test_graph_merge_it(self):
        timings = Times()
        count = 2**14

        gs = times(count, GraphInterface)
        timings.add("instance")

        for gl, gr in pairwise(gs):
            gl.connect(gr)

        timings.add("connect")

        self.assertEqual(gs[0].G.node_cnt, count)

        per_connect = timings.times["connect"] / count
        self.assertLess(timings.times["connect"], 500e-3)
        self.assertLess(timings.times["instance"], 200e-3)
        self.assertLess(per_connect, 25e-6)
        print(timings)
        print(f"----> Avg/connect: {per_connect*1e6:.2f} us")


if __name__ == "__main__":
    unittest.main()
