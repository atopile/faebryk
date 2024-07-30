import faebryk.library._F as F
from faebryk.core.core import Module


class MyComponent(Module):
    def __init__(self) -> None:
        super().__init__()

        class PARAMS(Module.PARAMS()):
            pass
            a = F.Range(100000.0, 100000.0)

        self.PARAMs = PARAMS(self)

        class _IFS(Module.IFS()):
            pass
            b = F.Electrical()
            d = F.Electrical()
            f = F.Electrical()

        self.IFs = _IFS(self)

        class _NODES(Module.NODES()):
            pass

        self.NODEs = _NODES(self)

        self.add_trait(F.has_designator_prefix_defined("U"))
        self.add_trait(
            F.has_defined_footprint(F.KicadFootprint("'SOT-23-5'", ["3", "5"]))
        )
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    self.IFs.d: "5",
                }
            )
        )




if __name__ == "__main__":
    from faebryk.libs.examples.buildutil import apply_design_to_pcb
    m = MyComponent()
    apply_design_to_pcb(m)
