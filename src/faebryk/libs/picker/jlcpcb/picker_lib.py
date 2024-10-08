import logging
from enum import Enum
from typing import Callable

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.e_series import E_SERIES_VALUES
from faebryk.libs.picker.jlcpcb.jlcpcb import (
    Component,
    ComponentQuery,
    MappingParameterDB,
)
from faebryk.libs.picker.picker import (
    DescriptiveProperties,
    PickError,
)
from faebryk.libs.util import KeyErrorAmbiguous, KeyErrorNotFound

logger = logging.getLogger(__name__)

# TODO add trait to module that specifies the quantity of the part
qty: int = 1

# TODO I really don't like this file
#   - lots of repetition
#       ->  .filter_by_traits(cmp)
#           .sort_by_price(qty)
#           .filter_by_module_params_and_attach(cmp, mapping, qty)
#   - should be classes instead of functions


# Generic pickers ----------------------------------------------------------------------


def str_to_enum[T: Enum](enum: type[T], x: str) -> F.Constant[T]:
    name = x.replace(" ", "_").replace("-", "_").upper()
    if name not in [e.name for e in enum]:
        raise ValueError(f"Enum translation error: {x}[={name}] not in {enum}")
    return F.Constant(enum[name])


def str_to_enum_func[T: Enum](enum: type[T]) -> Callable[[str], F.Constant[T]]:
    def f(x: str) -> F.Constant[T]:
        return str_to_enum(enum, x)

    return f


def find_component_by_lcsc_id(lcsc_id: str) -> Component:
    parts = ComponentQuery().filter_by_lcsc_pn(lcsc_id).get()

    if len(parts) < 1:
        raise KeyErrorNotFound(f"Could not find part with LCSC part number {lcsc_id}")

    if len(parts) > 1:
        raise KeyErrorAmbiguous(
            parts, f"Found multiple parts with LCSC part number {lcsc_id}"
        )

    return next(iter(parts))


def find_and_attach_by_lcsc_id(module: Module):
    """
    Find a part in the JLCPCB database by its LCSC part number
    """

    if not module.has_trait(F.has_descriptive_properties):
        raise PickError("Module does not have any descriptive properties", module)
    if "LCSC" not in module.get_trait(F.has_descriptive_properties).get_properties():
        raise PickError("Module does not have an LCSC part number", module)

    lcsc_pn = module.get_trait(F.has_descriptive_properties).get_properties()["LCSC"]

    try:
        part = find_component_by_lcsc_id(lcsc_pn)
    except KeyErrorNotFound as e:
        raise PickError(
            f"Could not find part with LCSC part number {lcsc_pn}", module
        ) from e
    except KeyErrorAmbiguous:
        raise PickError(f"Found no exact match for LCSC part number {lcsc_pn}", module)

    if part.stock < qty:
        raise PickError(
            f"Part with LCSC part number {lcsc_pn} has insufficient stock", module
        )

    part.attach(module, [])


def find_component_by_mfr(mfr: str, mfr_pn: str) -> Component:
    parts = (
        ComponentQuery()
        .filter_by_manufacturer_pn(mfr_pn)
        .filter_by_manufacturer(mfr)
        .filter_by_stock(qty)
        .sort_by_price()
        .get()
    )

    if len(parts) < 1:
        raise KeyErrorNotFound(
            f"Could not find part with manufacturer part number {mfr_pn}"
        )

    if len(parts) > 1:
        raise KeyErrorAmbiguous(
            parts, f"Found multiple parts with manufacturer part number {mfr_pn}"
        )

    return next(iter(parts))


def find_and_attach_by_mfr(module: Module):
    """
    Find a part in the JLCPCB database by its manufacturer part number
    """

    if not module.has_trait(F.has_descriptive_properties):
        raise PickError("Module does not have any descriptive properties", module)
    if (
        DescriptiveProperties.partno
        not in module.get_trait(F.has_descriptive_properties).get_properties()
    ):
        raise PickError("Module does not have a manufacturer part number", module)
    if (
        DescriptiveProperties.manufacturer
        not in module.get_trait(F.has_descriptive_properties).get_properties()
    ):
        raise PickError("Module does not have a manufacturer", module)

    mfr_pn = module.get_trait(F.has_descriptive_properties).get_properties()[
        DescriptiveProperties.partno
    ]
    mfr = module.get_trait(F.has_descriptive_properties).get_properties()[
        DescriptiveProperties.manufacturer
    ]

    try:
        parts = [find_component_by_mfr(mfr, mfr_pn)]
    except KeyErrorNotFound as e:
        raise PickError(
            f"Could not find part with manufacturer part number {mfr_pn}", module
        ) from e
    except KeyErrorAmbiguous as e:
        parts = e.duplicates

    for part in parts:
        try:
            part.attach(module, [])
            return
        except ValueError as e:
            logger.warning(f"Failed to attach component: {e}")
            continue

    raise PickError(
        f"Could not attach any part with manufacturer part number {mfr_pn}", module
    )


# Type specific pickers ----------------------------------------------------------------


def find_resistor(cmp: Module):
    """
    Find a resistor part in the JLCPCB database that matches the parameters of the
    provided resistor
    """
    assert isinstance(cmp, F.Resistor)

    mapping = [
        MappingParameterDB(
            "resistance",
            ["Resistance"],
            "Tolerance",
        ),
        MappingParameterDB(
            "rated_power",
            ["Power(Watts)"],
        ),
        MappingParameterDB(
            "rated_voltage",
            ["Overload Voltage (Max)"],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("Resistors", "Chip Resistor - Surface Mount")
        .filter_by_stock(qty)
        .filter_by_value(cmp.resistance, "Ω", E_SERIES_VALUES.E96)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_capacitor(cmp: Module):
    """
    Find a capacitor part in the JLCPCB database that matches the parameters of the
    provided capacitor
    """

    assert isinstance(cmp, F.Capacitor)

    mapping = [
        MappingParameterDB("capacitance", ["Capacitance"], "Tolerance"),
        MappingParameterDB(
            "rated_voltage",
            ["Voltage Rated"],
        ),
        MappingParameterDB(
            "temperature_coefficient",
            ["Temperature Coefficient"],
            transform_fn=lambda x: str_to_enum(
                F.Capacitor.TemperatureCoefficient, x.replace("NP0", "C0G")
            ),
        ),
    ]

    # TODO: add support for electrolytic capacitors.
    (
        ComponentQuery()
        .filter_by_category(
            "Capacitors", "Multilayer Ceramic Capacitors MLCC - SMD/SMT"
        )
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .filter_by_value(cmp.capacitance, "F", E_SERIES_VALUES.E24)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_inductor(cmp: Module):
    """
    Find an inductor part in the JLCPCB database that matches the parameters of the
    provided inductor.

    Note: When the "self_resonant_frequency" parameter is not ANY, only inductors
    from the HF and SMD categories are used.
    """

    assert isinstance(cmp, F.Inductor)

    mapping = [
        MappingParameterDB(
            "inductance",
            ["Inductance"],
            "Tolerance",
        ),
        MappingParameterDB(
            "rated_current",
            ["Rated Current"],
        ),
        MappingParameterDB(
            "dc_resistance",
            ["DC Resistance (DCR)", "DC Resistance"],
        ),
        MappingParameterDB(
            "self_resonant_frequency",
            ["Frequency - Self Resonant"],
        ),
    ]

    (
        ComponentQuery()
        # Get Inductors (SMD), Power Inductors, TH Inductors, HF Inductors,
        # Adjustable Inductors. HF and Adjustable are basically empty.
        .filter_by_category("Inductors", "Inductors")
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .filter_by_value(cmp.inductance, "H", E_SERIES_VALUES.E24)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_tvs(cmp: Module):
    """
    Find a TVS diode part in the JLCPCB database that matches the parameters of the
    provided diode
    """

    assert isinstance(cmp, F.TVS)

    # TODO: handle bidirectional TVS diodes
    # "Bidirectional Channels": "1" in extra['attributes']

    mapping = [
        MappingParameterDB(
            "forward_voltage",
            ["Breakdown Voltage"],
        ),
        # TODO: think about the difference of meaning for max_current between Diode
        # and TVS
        MappingParameterDB(
            "max_current",
            ["Peak Pulse Current (Ipp)@10/1000us"],
        ),
        MappingParameterDB(
            "reverse_working_voltage",
            ["Reverse Voltage (Vr)", "Reverse Stand-Off Voltage (Vrwm)"],
        ),
        MappingParameterDB(
            "reverse_leakage_current",
            ["Reverse Leakage Current", "Reverse Leakage Current (Ir)"],
        ),
        MappingParameterDB(
            "reverse_breakdown_voltage",
            ["Breakdown Voltage"],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("", "TVS")
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_diode(cmp: Module):
    """
    Find a diode part in the JLCPCB database that matches the parameters of the
    provided diode
    """

    assert isinstance(cmp, F.Diode)

    mapping = [
        MappingParameterDB(
            "forward_voltage",
            ["Forward Voltage", "Forward Voltage (Vf@If)"],
        ),
        MappingParameterDB(
            "max_current",
            ["Average Rectified Current (Io)"],
        ),
        MappingParameterDB(
            "reverse_working_voltage",
            ["Reverse Voltage (Vr)", "Reverse Stand-Off Voltage (Vrwm)"],
        ),
        MappingParameterDB(
            "reverse_leakage_current",
            ["Reverse Leakage Current", "Reverse Leakage Current (Ir)"],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("Diodes", "")
        .filter_by_stock(qty)
        .filter_by_value(cmp.max_current, "A", E_SERIES_VALUES.E3)
        .filter_by_value(cmp.reverse_working_voltage, "V", E_SERIES_VALUES.E3)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_led(cmp: Module):
    """
    Find a LED part in the JLCPCB database that matches the parameters of the
    provided LED
    """

    assert isinstance(cmp, F.LED)

    mapping = [
        MappingParameterDB(
            "color",
            ["Emitted Color"],
            transform_fn=str_to_enum_func(F.LED.Color),
        ),
        MappingParameterDB(
            "max_brightness",
            ["Luminous Intensity"],
        ),
        MappingParameterDB(
            "max_current",
            ["Forward Current"],
        ),
        MappingParameterDB(
            "forward_voltage",
            ["Forward Voltage", "Forward Voltage (VF)"],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("", "Light Emitting Diodes (LED)")
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_mosfet(cmp: Module):
    """
    Find a MOSFET part in the JLCPCB database that matches the parameters of the
    provided MOSFET
    """

    assert isinstance(cmp, F.MOSFET)

    mapping = [
        MappingParameterDB(
            "max_drain_source_voltage",
            ["Drain Source Voltage (Vdss)"],
        ),
        MappingParameterDB(
            "max_continuous_drain_current",
            ["Continuous Drain Current (Id)"],
        ),
        MappingParameterDB(
            "channel_type",
            ["Type"],
            transform_fn=str_to_enum_func(F.MOSFET.ChannelType),
        ),
        MappingParameterDB(
            "gate_source_threshold_voltage",
            ["Gate Threshold Voltage (Vgs(th)@Id)"],
        ),
        MappingParameterDB(
            "on_resistance",
            ["Drain Source On Resistance (RDS(on)@Vgs,Id)"],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("", "MOSFET")
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


def find_ldo(cmp: Module):
    """
    Find a LDO part in the JLCPCB database that matches the parameters of the
    provided LDO
    """

    assert isinstance(cmp, F.LDO)

    mapping = [
        MappingParameterDB(
            "output_polarity",
            ["Output Polarity"],
            transform_fn=str_to_enum_func(F.LDO.OutputPolarity),
        ),
        MappingParameterDB(
            "max_input_voltage",
            ["Maximum Input Voltage"],
        ),
        MappingParameterDB(
            "output_type",
            ["Output Type"],
            transform_fn=str_to_enum_func(F.LDO.OutputType),
        ),
        MappingParameterDB(
            "output_current",
            ["Output Current"],
        ),
        MappingParameterDB(
            "dropout_voltage",
            ["Dropout Voltage"],
        ),
        MappingParameterDB(
            "output_voltage",
            ["Output Voltage"],
        ),
        MappingParameterDB(
            "quiescent_current",
            [
                "Quiescent Current",
                "standby current",
                "Quiescent Current (Ground Current)",
            ],
        ),
    ]

    (
        ComponentQuery()
        .filter_by_category("", "LDO")
        .filter_by_stock(qty)
        .filter_by_traits(cmp)
        .sort_by_price(qty)
        .filter_by_module_params_and_attach(cmp, mapping, qty)
    )


# --------------------------------------------------------------------------------------

TYPE_SPECIFIC_LOOKUP = {
    F.Resistor: find_resistor,
    F.Capacitor: find_capacitor,
    F.Inductor: find_inductor,
    F.TVS: find_tvs,
    F.LED: find_led,
    F.Diode: find_diode,
    F.MOSFET: find_mosfet,
    F.LDO: find_ldo,
}
