# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Mechanical System Collection."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP

from model.hvac.ventilation_system import PhEnVentilationSystem

from openph.model.hvac.hot_water import PhEnHotWaterSystem


@dataclass
class PhEnHVAC:
    phpp: "PhEnPHPP"
    ventilation_system: PhEnVentilationSystem = field(init=False)
    hot_water_system: PhEnHotWaterSystem = field(init=False)

    def __post_init__(self):
        self.ventilation_system = PhEnVentilationSystem(phpp=self.phpp)
        self.hot_water_system = PhEnHotWaterSystem(phpp=self.phpp)
