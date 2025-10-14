# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Engineering Reference Constants"""

from dataclasses import dataclass
from functools import cached_property


@dataclass
class Constants:
    @cached_property
    def c_air(self):
        """0.33 Wh/(m³·K) The specific heat capacity of Air."""
        return 0.33

    @cached_property
    def kinematic_viscosity_air(self):
        """0.00001384 m²/s Kinematic viscosity of air at standard conditions."""
        return 0.00001384

    @cached_property
    def prandtl_number_air(self):
        """0.71 Prandtl number for air (ratio of momentum diffusivity to thermal diffusivity)"""
        return 0.71

    @cached_property
    def thermal_conductivity_air(self):
        """0.024915W/(m·K) Thermal conductivity of air at standard conditions."""
        return 0.024915
