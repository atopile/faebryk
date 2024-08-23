# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module


class PowerSwitchMOSFET(PowerSwitch):
    """
    Power switch using a MOSFET

    This power switch uses an NMOS when lowside, and a PMOS when highside.
    """

    def __init__(self, lowside: bool, normally_closed: bool) -> None:
        super().__init__(normally_closed=normally_closed)

        self.lowside = lowside

        # components

            mosfet = MOSFET()

        self.mosfet.channel_type.merge(
            F.Constant(
                MOSFET.ChannelType.N_CHANNEL
                if lowside
                else MOSFET.ChannelType.P_CHANNEL
            )
        )
        self.mosfet.saturation_type.merge(F.Constant(MOSFET.SaturationType.ENHANCEMENT))

        # pull gate
        # lowside     normally_closed   pull up
        # True        True              True
        # True        False             False
        # False       True              False
        # False       False             True
        self.logic_in.pulled.pull(
            lowside == normally_closed
        )

        # connect gate to logic
        self.logic_in.signal.connect(self.mosfet.gate)

        # passthrough non-switched side, bridge switched side
        if lowside:
            self.power_in.hv.connect(self.switched_power_out.hv)
            self.power_in.lv.connect_via(self.mosfet, self.switched_power_out.lv)
        else:
            self.power_in.lv.connect(self.switched_power_out.lv)
            self.power_in.hv.connect_via(self.mosfet, self.switched_power_out.hv)

        # TODO do more with logic
        #   e.g check reference being same as power
