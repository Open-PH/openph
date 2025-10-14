# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Fresh-Air Ventilation Load."""

from dataclasses import dataclass


@dataclass
class PhEnLoadVentilation:
    """Fresh-Air Ventilation airflows for a single Room."""

    supply_airflow_m3_h: float = 0.0
    exhaust_airflow_m3_h: float = 0.0
    transfer_airflow_m3_h: float = 0.0
