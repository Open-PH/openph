# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Internal Heat Gains (IHG)."""

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP


@dataclass
class IHG:
    phpp: "PhEnPHPP"

    @cached_property
    def specific_internal_heat_gain_rate_W_m2(self) -> float:
        """The total internal heat-gain rate [W/M2] from people, equipment, appliances, lighting)

        PHPP V10 | Data | C165
        =IF(Verification!F29>0,IF(Areas!L8/Verification!F29>50/(4.1-2.1),2.1+50*Verification!F29/Areas!L8,4.1),2.1)

        Units: W/m2
        """
        NUM_DWELLING_UNITS = 1  # TODO: Get Num-dwellings from model
        NON_RES = False
        if NON_RES:
            # TODO: Implement Non-Res IHG
            return 2.1
        else:
            if self.phpp.rooms.total_weighted_floor_area_m2 / NUM_DWELLING_UNITS > 50 / (4.1 - 2.1):
                return 2.1 + 50 * NUM_DWELLING_UNITS / self.phpp.rooms.total_weighted_floor_area_m2
            else:
                return 4.1

    @cached_property
    def average_annual_internal_heat_gain_W(self) -> float:
        """The total internal heat-gain rate [W] from people, equipment, appliances, lighting)."""
        return self.specific_internal_heat_gain_rate_W_m2 * self.phpp.rooms.total_weighted_floor_area_m2
