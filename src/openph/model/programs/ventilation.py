# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Program Class for organizing Fresh-Air Ventilation Data."""

from __future__ import annotations

from dataclasses import dataclass, field

from openph.model.loads import ventilation as vent_loads
from openph.model.schedules import ventilation as vent_schedules


@dataclass
class PhEnProgramVentilation:
    """A PhEn Program for the Fresh-Air Ventilation with a load and schedule."""

    display_name: str = "Unnamed_Ventilation_Program"
    load: vent_loads.PhEnLoadVentilation = field(default_factory=vent_loads.PhEnLoadVentilation)
    schedule: vent_schedules.PhEnScheduleVentilation = field(default_factory=vent_schedules.PhEnScheduleVentilation)
