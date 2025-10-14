# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP


@dataclass(frozen=True)
class PhEnInfiltration:
    phpp: "PhEnPHPP"

    wind_coefficient_e: float = 0.07
    wind_coefficient_f: float = 15.0
    airtightness_n50: float = 0.6

    @cached_property
    def n_v_res(self) -> float:
        """

        PHPP V10 | Ventilation | M27

        =IF(OR($M$8=0,M19=0,M23=0,$M$22=0),"",$M$22/$M$8*M23*M19/(1+M20/M19*(M26/M23)^2))

        Returns:
            ACH
        """
        VentilationM26 = 0.0  # TODO: Calc excess mech extract air ach
        return (
            self.phpp.rooms.total_net_interior_volume_m3
            / self.phpp.rooms.total_ventilated_volume_m3
            * self.airtightness_n50
            * self.wind_coefficient_e
            / (
                1
                + self.wind_coefficient_f
                / self.wind_coefficient_e
                * (VentilationM26 / self.phpp.infiltration.airtightness_n50) ** 2
            )
        )
