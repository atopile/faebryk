import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.reference import reference
from faebryk.core.trait import Trait


class Symbol(Module):
    """
    Symbols represent a symbol instance and are bi-directionally
    linked with the module they represent via the `has_linked` trait.
    """

    class Pin(ModuleInterface):
        represents = reference(ModuleInterface)

        class has_pin(F.has_reference[F.Electrical].impl()):
            """
            Attach to an ElectricalInterface to point back at the pin
            """

    class TraitT(Trait): ...

    class has_symbol(F.has_reference[Module].impl()):
        """
        Attach to an Module to point back at the pin
        """

    class has_kicad_symbol(TraitT.decless()):
        """
        If a symbol has this trait, then the symbol has a matching KiCAD symbol
        :param symbol_name: The full name of the KiCAD symbol including the library name
        """

        def __init__(self, symbol_name: str):
            super().__init__()
            self.symbol_name = symbol_name

    pins: dict[str, Pin]
    represents = reference(Module)

    @classmethod
    def with_component(cls, component: Module, pin_map: dict[str, ModuleInterface]):
        sym = cls()
        sym.represents = component
        component.add(cls.has_symbol(sym))

        sym.pins = {}
        for pin_name, e_pin in pin_map.items():
            pin = cls.Pin()
            pin.represents = e_pin
            e_pin.add(cls.Pin.has_pin(pin))
            sym.pins[pin_name] = pin

        return sym
