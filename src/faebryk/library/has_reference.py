from faebryk.core.node import Node
from faebryk.core.reference import Reference
from faebryk.core.trait import Trait


class has_reference[T: Node](Trait.decless()):
    """Trait-attached reference"""

    reference: T = Reference()

    def __init__(self, reference: T):
        super().__init__()
        self.reference = reference

    # TODO: extend this class with support for other trait-types
