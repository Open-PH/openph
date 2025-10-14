# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Occupancy Schedule."""

from dataclasses import dataclass


@dataclass
class PhEnScheduleOccupancy:
    """A PH-Energy Schedule for the Occupancy."""

    id_num: int = 0
    name: str = "__unnamed_occupancy_schedule__"
    identifier: str = "_identifier_"
