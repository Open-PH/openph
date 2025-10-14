# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEn Opaque and Aperture Constructions."""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhEnConstructionOpaque:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    u_value: float = 1.0  # W/m2k


@dataclass(frozen=True)
class PhEnWindowFrameElement:
    width: float = 0.1  # m
    u_value: float = 1.0  # W/m2k
    psi_glazing: float = 0.00  # W/mk
    psi_install: float = 0.00  # W/mk


@dataclass(frozen=True)
class PhEnGlazing:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    u_value: float = 1.0
    g_value: float = 0.4


@dataclass(frozen=True)
class PhEnConstructionAperture:
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    id_num: int = 0
    display_name: str = ""
    glazing_type_display_name: str = ""
    frame_type_display_name: str = ""

    glazing: PhEnGlazing = field(default_factory=PhEnGlazing)
    frame_top: PhEnWindowFrameElement = field(default_factory=PhEnWindowFrameElement)
    frame_bottom: PhEnWindowFrameElement = field(default_factory=PhEnWindowFrameElement)
    frame_left: PhEnWindowFrameElement = field(default_factory=PhEnWindowFrameElement)
    frame_right: PhEnWindowFrameElement = field(default_factory=PhEnWindowFrameElement)
