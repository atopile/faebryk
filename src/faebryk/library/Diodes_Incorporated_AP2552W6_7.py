# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.core.parameter import Parameter
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.picker.picker import DescriptiveProperties
from faebryk.libs.units import P, Quantity  # noqa: F401

logger = logging.getLogger(__name__)


class Diodes_Incorporated_AP2552W6_7(Module):
    """
    Power Distribution Switch. Mostly used in USB applications.
    2.7V~5.5V 70mΩ 2.1A SOT-26
    """

    def set_current_limit(self, current: Parameter[Quantity]) -> None:
        self.current_limit.merge(current)

        current_limit_setting_resistor = self.ilim.get_trait(
            F.ElectricLogic.can_be_pulled
        ).pull(up=False)

        # TODO:
        # self.ilim.connect_via(
        #    current_limit_setting_resistor, self.power_in.lv
        # )

        # Rlim is in Kohm
        # current is in mA
        # Rlim_min = (20.08 / (current)) ^ (1 / 0.956) * P.kohm
        # Rlim_max = (20.08 / (current)) ^ (1 / 0.904) * P.kohm

        # TODO: Rlim = Range(Rlim_min, Rlim_max)
        Rlim = F.Constant(51 * P.kohm)  # ~0.52A typical current limit
        assert Rlim.is_subset_of(
            F.Range(10 * P.kohm, 210 * P.kohm)
        ), f"{self.get_full_name()} Rlim must be in the range 10kOhm to 210kOhm but is {Rlim}"  # noqa: E501

        current_limit_setting_resistor.resistance.merge(Rlim)
        Rlim = F.Range(10 * P.kohm, 210 * P.kohm)

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power_in: F.ElectricPower
    power_out: F.ElectricPower
    enable: F.ElectricLogic
    fault: F.ElectricLogic
    ilim: F.ElectricLogic  # TODO: hack to add resistor, should be Electrical()

    current_limit: F.TBD[Quantity]
    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    descriptive_properties = L.f_field(F.has_descriptive_properties_defined)(
        {
            DescriptiveProperties.manufacturer: "Diodes Incorporated",
            DescriptiveProperties.partno: "AP2552W6-7",
        }
    )
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Diodes-Incorporated-AP2552W6-7_C441824.pdf"  # noqa: E501
    )

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={
                self.power_in.hv: ["IN"],
                self.power_in.lv: ["GND"],
                self.enable.signal: ["EN/EN#"],
                self.fault.signal: ["FAULT#"],
                self.ilim.signal: ["ILIM"],
                self.power_out.hv: ["OUT"],
            },
            accept_prefix=False,
            case_sensitive=False,
        )

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.power_in, self.power_out)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    @L.rt_field
    def has_defined_layout(self):
        # pcb layout
        Point = has_pcb_position.Point
        L = has_pcb_position.layer_type
        LVL = LayoutTypeHierarchy.Level

        layouts = [
            LVL(
                mod_type=F.Resistor,
                layout=LayoutAbsolute(
                    Point((0, -3, 90, L.NONE)),
                ),
            ),
            LVL(
                mod_type=F.Capacitor,
                layout=LayoutExtrude(
                    base=Point((-0.95, 3.25, 270, L.NONE)),
                    vector=(-6.5, 0, 180),
                    dynamic_rotation=True,
                ),
            ),
        ]
        return F.has_pcb_layout_defined(LayoutTypeHierarchy(layouts))

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        pass
