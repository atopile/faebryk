from collections import defaultdict

from faebryk.core.graphinterface import GraphInterfaceReference
from faebryk.core.link import LinkPointer
from faebryk.core.node import Node, constructed_field


class Reference[O: Node](constructed_field):
    """
    Create a simple reference to other nodes that are properly encoded in the graph.
    """

    class UnboundError(Exception):
        """Cannot resolve unbound reference"""

    def __init__(self, out_type: type[O] | None = None):
        self.gifs: dict[Node, GraphInterfaceReference] = defaultdict(
            GraphInterfaceReference
        )
        self.points_to: dict[Node, O] = {}

        def get(instance: Node) -> O:
            if instance not in self.gifs:
                raise Reference.UnboundError

            my_gif = self.gifs[instance]

            try:
                return my_gif.get_reference()
            except GraphInterfaceReference.UnboundError as ex:
                raise Reference.UnboundError from ex

        def set(instance: Node, value: O):
            if instance in self.points_to:
                # TypeError is also raised when attempting to assign
                # to an immutable (eg. tuple)
                raise TypeError(
                    f"{self.__class__.__name__} already set and are immutable"
                )

            if out_type is not None and not isinstance(value, out_type):
                raise TypeError(f"Expected {out_type} got {type(value)}")

            self.points_to[instance] = value

            # if we've already been graph-constructed
            # then immediately attach our gif to what we're referring to
            # if not, this is done in the construction
            if instance._init:
                self.gifs[instance].connect(value.self_gif, LinkPointer)

        property.__init__(self, get, set)

    def __construct__(self, obj: Node) -> None:
        gif = obj.add(self.gifs[obj])

        # if what we're referring to is set, then immediately also connect the link
        if points_to := self.points_to.get(obj):
            gif.connect(points_to.self_gif, LinkPointer)

        # don't attach anything additional to the Node during field setup
        return None


def reference[O: Node](out_type: type[O] | None = None) -> O | Reference:
    """
    Create a simple reference to other nodes properly encoded in the graph.

    This final wrapper is primarily to fudge the typing.
    """
    return Reference(out_type=out_type)
