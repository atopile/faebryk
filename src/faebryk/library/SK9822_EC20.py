# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module







class SK9822_EC20(Module):
    """
    SK9822 is a two-wire transmission channel three
    (RGB) driving intelligent control circuit and
    the light emitting circuit in one of the LED light
    source control. Products containing a signal
    decoding module, data buffer, a built-in F.Constant
    current circuit and RC oscillator; CMOS, low
    voltage, low power consumption; 256 level grayscale
    PWM adjustment and 32 brightness adjustment;
    use the double output, Data and synchronization of
    the CLK signal, connected in series each wafer
    output action synchronization.
    """



        # interfaces

            power: F.ElectricPower
            sdo: F.ElectricLogic
            sdi: F.ElectricLogic
            cko: F.ElectricLogic
            ckl: F.ElectricLogic

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.sdo.signal,
                    "2": x.power.lv,
                    "3": x.sdi.signal,
                    "4": x.ckl.signal,
                    "5": x.power.hv,
                    "6": x.cko.signal,
                }
            )
        )

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))

        self.add_trait(
            has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/2110250930_OPSCO-Optoelectronics-SK9822-EC20_C2909059.pdf"
            )
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("LED")
