# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P


class CBM9002A_56ILG_ReferenceDesign(Module):
    """
    Minimal working example for the CBM9002A_56ILG
    """

    class ResetCircuit(Module):
        """low-pass and protection for reset"""

        diode: F.Diode
        cap: F.Capacitor
        logic: F.ElectricLogic

        def __preinit__(self):
            self.logic.signal.connect_via(self.diode, self.logic.reference.hv)
            self.logic.pulled.pull(up=True)
            self.logic.signal.connect_via(self.cap, self.logic.reference.lv)

            self.cap.capacitance.merge(F.Range.from_center_rel(1 * P.uF, 0.05))

            self.diode.forward_voltage.merge(F.Range(715 * P.mV, 1.5 * P.V))
            self.diode.reverse_leakage_current.merge(F.Range.upper_bound(1 * P.uA))
            self.diode.current.merge(F.Range.from_center_rel(300 * P.mA, 0.05))
            self.diode.max_current.merge(F.Range.lower_bound(1 * P.A))

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    mcu: F.CBM9002A_56ILG
    oscillator: F.Crystal_Oscillator
    reset_circuit: ResetCircuit

    PA = L.list_field(8, F.ElectricLogic)
    PB = L.list_field(8, F.ElectricLogic)
    PD = L.list_field(8, F.ElectricLogic)
    usb: F.USB2_0
    i2c: F.I2C

    avcc: F.ElectricPower
    vcc: F.ElectricPower

    rdy = L.list_field(2, F.ElectricLogic)
    ctl = L.list_field(3, F.ElectricLogic)
    reset: F.ElectricLogic
    wakeup: F.ElectricLogic

    ifclk: F.ElectricLogic
    clkout: F.ElectricLogic
    xtalin: F.Electrical
    xtalout: F.Electrical

    # ----------------------------------------
    #                traits
    # ----------------------------------------

    # ----------------------------------------
    #                connections
    # ----------------------------------------
    def __preinit__(self):
        self.connect_interfaces_by_name(self.mcu, allow_partial=True)

        # crystal oscillator
        self.oscillator.xtal_if.gnd.connect(self.vcc.lv)
        self.oscillator.xtal_if.xin.connect(self.xtalin)
        self.oscillator.xtal_if.xout.connect(self.xtalout)

        self.reset_circuit.logic.connect(self.mcu.reset)

        self.avcc.decoupled.decouple()
        self.vcc.decoupled.decouple()

        # ----------------------------------------
        #               Parameters
        # ----------------------------------------

        self.oscillator.crystal.frequency.merge(
            F.Range.from_center_rel(24 * P.Mhertz, 0.05)
        )
        self.oscillator.crystal.frequency_tolerance.merge(
            F.Range(0 * P.ppm, 20 * P.ppm)
        )
