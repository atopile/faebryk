# %%
"""
The objective is to make parameter's operations bi-directional.

"""

from scipy.optimize import minimize, root_scalar

from faebryk.core.graphinterface import GraphInterface
from faebryk.core.module import Module
from faebryk.core.graph import Graph
from faebryk.core.util import get_nodes_from_gifs
from faebryk.libs.util import FuncSet
from faebryk.exporters.visualize.interactive_graph import interactive_graph
from faebryk.core.parameter import Parameter
from faebryk.library import has_placticity
from faebryk.library.Constant import Constant
from faebryk.library.Operation import Operation
from faebryk.library.Range import Range
from faebryk.library.TBD import TBD
from faebryk.core.node import Node, d_field, rt_field
from faebryk.libs.util import bfs_visit
from faebryk.library.has_placticity import has_placticity
from faebryk.library.has_placiticity_defined import has_placticity_defined


class DemoApp(Module):
    # dependent
    a: Parameter = d_field(lambda: Range(0, 5))
    b: TBD
    c: Parameter = rt_field(lambda self: self.a + self.b)

    def __preinit__(self):
        super().__preinit__()
        self.a.add(has_placticity_defined(lambda _: 5))
        self.b.merge(Range(1, 4))

d = DemoApp()
g = d.get_graph()

# %%
def _hide_me():
    pass
    # %%
    interactive_graph(g)

# %%
def get_entangled_params(p: Parameter):
    def _neighbours(p: Parameter):
        assert isinstance(p, Parameter)
        return get_nodes_from_gifs(
            (
                p.depends_on.get_direct_connections()
                | p.depended_on_by.get_direct_connections()
                | p.narrows.get_direct_connections()
                | p.narrowed_by.get_direct_connections()
            )
        )

    return bfs_visit(_neighbours, [p])

entangled_params = get_entangled_params(d.c)
entangled_params

# %%
plasticity = [
    p.get_trait(has_placticity)
    for p in entangled_params
    if p.has_trait(has_placticity)
]
plasticity

# %%
independant_params = FuncSet[Parameter]([
    p.get_most_narrow() for p in entangled_params
])
for param in independant_params:
    print(param)

# %%
def _is_plastic(p: Parameter) -> bool:
    """
    For a param to be considered plastic it and all of its narrowing chain 
    """

# %%
def _neighbours(p: Parameter):
    assert isinstance(p, Parameter)
    print(n := p.get_most_narrow().depends_on.get_direct_connections())
    return get_nodes_from_gifs(n)

for p in bfs_visit(_neighbours, [d.c]):
    print(p)

# %%
d.c.get_most_narrow()
# %%
