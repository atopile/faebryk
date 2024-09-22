import faebryk.library._F as F
from faebryk.core.node import Node
from faebryk.core.trait import Trait


class has_reference[T: Node](Trait.decless()):
    """Trait-attached reference"""

    reference: T = F.Reference()

    def __init__(self, reference: T):
        super().__init__()
        self.reference = reference

    # TODO: extend this class with support for other trait-types
