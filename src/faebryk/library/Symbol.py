import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.trait import Trait


class Symbol(Module):
    """
    Symbols represent a symbol instance and are bi-directionally
    linked with the module they represent via the `has_linked` trait.
    """

    class Pin(ModuleInterface):
        represents: "ModuleInterface"

        class TraitT(Trait): ...

        class has_symbol(TraitT):
            """
            This trait binds a symbol to the module it represents, and visa-versa.
            """

            symbol: "Symbol.Pin"

        class has_symbol_defined(has_symbol.impl()):
            def __init__(self, symbol: "Symbol.Pin"):
                super().__init__()
                self.symbol = symbol

    class TraitT(Trait): ...

    class has_symbol(Module.TraitT):
        """
        This trait binds a symbol to the module it represents, and visa-versa.
        """

        symbol: "Symbol"

    class has_symbol_defined(has_symbol.impl()):
        def __init__(self, symbol: "Symbol"):
            super().__init__()
            self.symbol = symbol

    class has_kicad_symbol(TraitT):
        """
        If a symbol has this trait, then the symbol has a matching KiCAD symbol
        :param symbol_name: The full name of the KiCAD symbol including the library name
        """

        symbol_name: str

    class has_kicad_symbol_defined(has_kicad_symbol.impl()):
        def __init__(self, symbol_name: str):
            super().__init__()
            self.symbol_name = symbol_name

    pins: dict[str, Pin]
    represents: Module

    @classmethod
    def with_component(cls, component: Module, pin_map: dict[str, ModuleInterface]):
        sym = cls()
        sym.represents = component
        component.add(cls.has_symbol_defined(sym))

        sym.pins = {}
        for pin_name, e_pin in pin_map.items():
            pin = cls.Pin()
            pin.represents = e_pin
            e_pin.add(cls.Pin.has_symbol_defined(pin))
            sym.pins[pin_name] = pin

        return sym
