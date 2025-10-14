# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Enum classes."""

from collections.abc import Iterator
from enum import Enum, auto


class Hemisphere(Enum):
    NORTH = auto()
    SOUTH = auto()


class CardinalOrientation(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()
    HORIZONTAL = auto()

    def __iter__(self) -> Iterator["CardinalOrientation"]:
        return iter(self)

    def __str__(self) -> str:
        return self.name


class Season(Enum):
    WINTER = auto()
    SUMMER = auto()


class ComponentFaceType(Enum):
    NONE = 0
    WALL = 1
    FLOOR = 2
    ROOF_CEILING = 3
    AIR_BOUNDARY = 3
    WINDOW = 4
    ADIABATIC = 5
    CUSTOM = 6


class ComponentExposureExterior(Enum):
    NONE = 0
    EXTERIOR = -1
    GROUND = -2
    SURFACE = -3
