# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Dataclasses for Opaque-Surfaces and Apertures (Windows/Doors)."""

import math
from dataclasses import dataclass, field
from functools import cached_property

from openph.model import constructions, enums


# -----------------------------------------------------------------------------
# -- Exceptions
class MissingConstructionError(Exception):
    """Raised when a Surface or Aperture is missing a Construction."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# -----------------------------------------------------------------------------
# -- Opaque Surfaces
@dataclass
class PhEnOpaqueSurfaceHeatGains:
    """Heat-gains properties and methods for a single Opaque-Surface in the PHPP.

    PHPP-10 | Areas | BP41:BU140
    """

    host: "PhEnOpaqueSurfaceSeasonalHeatGains"
    season: enums.Season
    _shading_factor: float | None = None

    # -- Constants
    r_se: float = 0.04  # ----- [m2k/W] Areas Tab | Cell BP30
    h_rad_e: float = 5.0  # --- [W/m2k] Areas Tab | Cell BS30
    h_kon_e: float = 15.0  # -- [W/m2k] Areas Tab | Cell BR30
    dirt: float = 0.95

    @cached_property
    def host_surface(self) -> "PhEnOpaqueSurface":
        return self.host.host

    @property
    def shading_factor(self) -> float:
        if not self._shading_factor:
            return 0.5
        else:
            return self._shading_factor

    @shading_factor.setter
    def shading_factor(self, value: float) -> None:
        self._shading_factor = value

    @cached_property
    def eff_solar_gain_area_m2(self) -> float:
        """Return the surface's effective solar-gain-area [m2], considering shading and surface-absorptance.
        For opaque-surfaces, this is always 0
        """
        return 0.0

    @cached_property
    def eff_heat_gain_area_m2(self) -> float:
        """Returns the surface's effective heat-gain-area [m2], considering shading and surface-absorptance.

        PHPP-10 | Areas | Column 'BP'
        = 1 / (AJ41 * $BQ$30 + $BR$30) / (1 / AC41 - $BP$30 + 1/ (AJ41 * $BQ$30 + $BR$30)) * AI41 * AH41 * Z41
        """
        if self.host_surface.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            _part_1 = self.host_surface.emissivity * self.h_rad_e + self.h_kon_e
            _part_2 = 1 / self.host_surface.u_value_W_m2_k - self.r_se + 1 / _part_1

            return (
                1
                / _part_1
                / _part_2
                * self.host_surface.absorptance
                * self.host_surface.heat_gain.winter.shading_factor
                * self.host_surface.net_area_m2
            )

    @cached_property
    def sky_view(self) -> float:
        """Returns the surface's 'View Factor to Sky' [%] value.

        PHPP-10 | Areas | Column 'BQ'
        = 0.5 * (1 + COS( RADIANS(AF42) ))
        """

        return 0.5 * (1 + math.cos(math.radians(self.host_surface.angle_from_horizontal)))

    @cached_property
    def alpha_sky(self) -> float:
        """Returns the surface's 'Alpha Sky' [W/m²K] value.

        PHPP-10 | Areas | Column 'BR'
        = AJ42 * AH42 * BQ42 * $BQ$30
        """

        return (
            self.host_surface.emissivity
            * self.host_surface.heat_gain.winter.shading_factor
            * self.sky_view
            * self.h_rad_e
        )

    @cached_property
    def alpha_air(self) -> float:
        """Returns the surface's 'Alpha Air' [W/m²K] value.

        PHPP-10 | Areas | Column 'BS'
        = $BR$30 + AJ41 * (1-AH41) * BQ41) * $BQ$30
        """

        return (
            self.h_kon_e
            + self.host_surface.emissivity
            * (1 - self.host_surface.heat_gain.winter.shading_factor * self.sky_view)
            * self.h_rad_e
        )

    @cached_property
    def convective_factor_W_K(self) -> float:
        """Returns the surface's 'Air Conductance' factor [W/K].

        PHPP-10 | Areas | Column 'BU'
        = (BS42 / (1 + (BR42 + BS42) * (1 / AC42 - $BP$30)) - AC42) * Z42

        Units: W/K
        """
        if self.host_surface.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            _part_1 = self.alpha_sky + self.alpha_air
            _part_2 = 1 / self.host_surface.u_value_W_m2_k - self.r_se
            _part_3 = self.alpha_air / (1 + _part_1 * _part_2) - self.host_surface.u_value_W_m2_k
            result = _part_3 * self.host_surface.net_area_m2
            return result

    @cached_property
    def radiative_factor_W_K(self) -> float:
        """Returns the surface's 'Sky Conductance' factor [W/K].

        PHPP-10 | Areas | Column 'BT'
        = BR42 / (1 + (BR42 + BS42) * ( 1 / AC42 - $BP$30)) * Z42
        """
        if self.host_surface.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            return (
                self.alpha_sky
                / (1 + (self.alpha_sky + self.alpha_air) * (1 / self.host_surface.u_value_W_m2_k - self.r_se))
                * self.host_surface.net_area_m2
            )


@dataclass
class PhEnOpaqueSurfaceSeasonalHeatGains:
    """Wrapper for enums.Seasonal (Winter / Summer) Heat-Gain properties and methods."""

    host: "PhEnOpaqueSurface"

    def __post_init__(self) -> None:
        self.winter = PhEnOpaqueSurfaceHeatGains(self, enums.Season.WINTER)
        self.summer = PhEnOpaqueSurfaceHeatGains(self, enums.Season.SUMMER)


@dataclass
class PhEnOpaqueSurface:
    """A single Opaque Surface in the PHPP.

    PHPP-10 | Areas | L41:BG140
    """

    construction: constructions.PhEnConstructionOpaque
    id_num: int = 0
    display_name: str = "_unnamed_surface_"
    quantity: int = 1
    area_m2: float = 0.0
    angle_from_horizontal: float = 0.0
    cardinal_orientation_angle: float = 0.0  # Degrees from North
    face_type: enums.ComponentFaceType = field(default=enums.ComponentFaceType.WINDOW)
    exposure_exterior: enums.ComponentExposureExterior = field(default=enums.ComponentExposureExterior.EXTERIOR)

    # -- Child surfaces (windows and doors)
    apertures: list["PhEnApertureSurface"] = field(default_factory=list)

    # -- Temporary Constants
    # TODO: Set Emissivity and Absorptance as part of the Construction
    emissivity: float = 0.9
    absorptance: float = 0.6

    def __post_init__(self) -> None:
        self.heat_gain = PhEnOpaqueSurfaceSeasonalHeatGains(self)

    def add_aperture(self, aperture: "PhEnApertureSurface | None") -> None:
        """Add a child PhEnSurface_Aperture to the PhEnSurface_Opaque."""
        if aperture is not None:
            aperture.host = self
            self.apertures.append(aperture)

    @cached_property
    def aperture_area_m2(self) -> float:
        """The total area of all the apertures in the surface (m2)."""
        return sum([aperture.net_area_m2 for aperture in self.apertures])

    @cached_property
    def net_area_m2(self) -> float:
        """The net area (less the apertures) of the surface (m2)."""
        return self.area_m2 - self.aperture_area_m2

    @cached_property
    def u_value_W_m2_k(self) -> float:
        """The U-Value of the Component's Construction."""
        return self.construction.u_value

    @cached_property
    def heat_loss_factor_W_K(self) -> float:
        """The UxA (net) value of the surface (W/K)."""
        return self.net_area_m2 * self.u_value_W_m2_k

    @cached_property
    def cardinal_orientation_type(self) -> enums.CardinalOrientation:
        """The cardinal orientation (North, South, East, West) of the surface.

        PHPP-10 | Areas | AG41:AG140
        """
        if abs(math.sin(math.radians(self.angle_from_horizontal))) <= 0.5:
            return enums.CardinalOrientation.HORIZONTAL

        if math.sin(math.radians(self.cardinal_orientation_angle + 45)) >= 0.0:
            if math.cos(math.radians(self.cardinal_orientation_angle + 45)) >= 0.0:
                return enums.CardinalOrientation.NORTH
            else:
                return enums.CardinalOrientation.EAST
        else:
            if math.cos(math.radians(self.cardinal_orientation_angle + 45)) >= 0.0:
                return enums.CardinalOrientation.WEST
            else:
                return enums.CardinalOrientation.SOUTH

    @cached_property
    def cardinal_orientation_name(self) -> str:
        """The cardinal orientation name ("North", "South", "East", "West") of the surface."""
        return self.cardinal_orientation_type.name


# -----------------------------------------------------------------------------
# -- Aperture Surfaces
@dataclass
class PhEnApertureHeatGains:
    """Heat-gains properties and methods for a single Aperture-Surface in the PHPP."""

    host: "PhEnApertureSurfaceSeasonalHeatGains"
    season: enums.Season
    _shading_factor: float | None = None

    # -- Constants
    r_se: float = 0.04  # ---- [m2k/W] Areas Tab | Cell BP30
    h_rad_e: float = 5.0  # -- [W/m2k] Areas Tab | Cell BS30
    h_kon_e: float = 15.0  # - [W/m2k] Areas Tab | Cell BR30
    dirt: float = 0.95

    @property
    def shading_factor(self) -> float:
        if not self._shading_factor:
            if self.season == enums.Season.SUMMER:
                return 0.75
            else:
                return 1.0
        else:
            return self._shading_factor

    @shading_factor.setter
    def shading_factor(self, value: float) -> None:
        self._shading_factor = value

    @cached_property
    def non_perpendicular_radiation(self) -> float:
        if self.season == enums.Season.SUMMER:
            return 0.90
        else:
            return 0.85

    @cached_property
    def aperture(self) -> "PhEnApertureSurface":
        return self.host.host

    @cached_property
    def total_reduction_factor(self) -> float:
        """The total Summer reduction factor of the aperture."""
        return self.aperture.glazing_fraction * self.shading_factor * self.dirt * self.non_perpendicular_radiation

    @cached_property
    def eff_solar_gain_area_m2(self) -> float:
        """Return the aperture's Summer effective solar-gain-area [m2] considering reduction factors."""
        return self.total_reduction_factor * self.aperture.g_value * self.aperture.area_m2

    @cached_property
    def eff_heat_gain_area_m2(self) -> float:
        """Return the aperture's effective heat-gain-area [m2] which is used
        to calculate the solar-heating of the frame. Note that this used to
        assess the transmission gains of the frame, NOT the solar radiation through
        the glazing.

        PHPP-10 | Windows | 'JR'
        = L23 / ($O$19 * $JS$18 + $JU$18) / (1 / JQ23 - $JR$18 + 1 / ($O$19 * $JS$18 + $JT$18)) * $O$18 * DS23 / AX23
        """
        if self.aperture.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            _part_1 = self.aperture.emissivity * self.h_rad_e + self.h_kon_e
            _part_2 = 1 / self.aperture.u_value_wm2k - self.r_se + 1 / _part_1

            return (
                self.aperture.quantity
                / _part_1
                / _part_2
                * self.aperture.absorptance
                * self.aperture.frame_area_m2
                / self.aperture.glazing_area_m2
            )

    @cached_property
    def sky_view(self) -> float:
        """Returns the surface's 'View Factor to Sky' [%] value.

        PHPP-10 | Windows | Column 'JS'
        = 0.5 * (1 + COS( RADIANS(AF42) )) * AVERAGE(Shading!AO23, Shading!AS23)
        """
        avg_shading_factor = (self.host.winter.shading_factor + self.host.summer.shading_factor) / 2
        return 0.5 * (1 + math.cos(math.radians(self.aperture.angle_from_horizontal))) * avg_shading_factor

    @cached_property
    def alpha_sky(self) -> float:
        """Returns the surface's 'Alpha Sky' [W/m²K] value.

        PHPP-10 | Windows | Column 'JT'
        = $O$19 * JS23 * $JS$18
        """

        return self.aperture.emissivity * self.sky_view * self.h_rad_e

    @cached_property
    def alpha_air(self) -> float:
        """Returns the surface's 'Alpha Air' [W/m²K] value.

        PHPP-10 | Windows | Column 'JU'
        = $JT$18 + $O$19 * (1-JS23) * $JS$18
        """

        return self.h_kon_e + self.aperture.emissivity * (1 - self.sky_view) * self.h_rad_e

    @cached_property
    def convective_factor_W_K(self) -> float:
        """Returns the surface's 'Air Conductance' factor [W/K].

        PHPP-10 | Areas | Column 'JW'
        =  L23 * (JU23 / (1 + (JT23 + JU23) * (1 / JQ23 - $JR$18))- JQ23) * DS23

        Units: W/K
        """
        if self.aperture.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            return (
                self.aperture.quantity
                * (
                    self.alpha_air
                    / (1 + (self.alpha_air + self.alpha_sky) * (1 / self.aperture.u_value_wm2k - self.r_se))
                    - self.aperture.u_value_wm2k
                )
                * self.aperture.frame_area_m2
            )

    @cached_property
    def radiative_factor_W_K(self) -> float:
        """Returns the surface's 'Sky Conductance' factor [W/K].

        PHPP-10 | Windows | Column 'JV'
        = L23 * JT23 / (1 + (JT23 + JU23) * (1 / JQ23 - $JR$18)) * DS23
        """
        if self.aperture.exposure_exterior == enums.ComponentExposureExterior.GROUND:
            return 0.0
        else:
            return (
                self.aperture.quantity
                * self.alpha_sky
                / (1 + (self.alpha_sky + self.alpha_air) * (1 / self.aperture.u_value_wm2k - self.r_se))
                * self.aperture.frame_area_m2
            )


@dataclass
class PhEnApertureSurfaceSeasonalHeatGains:
    """Wrapper for enums.Seasonal Heat_Gains properties and methods."""

    host: "PhEnApertureSurface"

    def __post_init__(self) -> None:
        self.winter = PhEnApertureHeatGains(self, enums.Season.WINTER)
        self.summer = PhEnApertureHeatGains(self, enums.Season.SUMMER)


@dataclass
class PhEnApertureSurface:
    """A single Aperture (Window or Door) in the PHPP.

    PHPP-10 | Windows | L23:ET174
    """

    host: PhEnOpaqueSurface
    construction: constructions.PhEnConstructionAperture

    id_num: int = 0
    display_name: str = "_unnamed_aperture_"
    quantity: int = 1
    height_m: float = 0.0
    width_m: float = 0.0
    face_type: enums.ComponentFaceType = field(default=enums.ComponentFaceType.WALL)
    exposure_exterior: enums.ComponentExposureExterior = field(default=enums.ComponentExposureExterior.EXTERIOR)

    emissivity: float = 0.9
    absorptance: float = 0.6

    def __post_init__(self) -> None:
        self.heat_gain = PhEnApertureSurfaceSeasonalHeatGains(self)

    @cached_property
    def total_glazing_heat_flow(self) -> float:
        return self.construction.glazing.u_value * self.glazing_area_m2

    @cached_property
    def total_frame_heat_flow(self) -> float:
        """The total Frame-Heat-Flow (W/K) of the Aperture."""
        top_right_corner_area_m2 = (self.construction.frame_top.width * self.construction.frame_right.width) / 2
        top_left_corner_area_m2 = (self.construction.frame_top.width * self.construction.frame_left.width) / 2
        bottom_right_corner_area_m2 = (self.construction.frame_bottom.width * self.construction.frame_right.width) / 2
        bottom_left_corner_area_m2 = (self.construction.frame_bottom.width * self.construction.frame_left.width) / 2

        top_area_m2 = (
            (self.construction.frame_top.width * self.glazing_width_m)
            + top_left_corner_area_m2
            + top_right_corner_area_m2
        )
        bottom_area_m2 = (
            (self.construction.frame_bottom.width * self.glazing_width_m)
            + top_left_corner_area_m2
            + top_right_corner_area_m2
        )
        left_area_m2 = (
            (self.construction.frame_left.width * self.glazing_height_m)
            + top_left_corner_area_m2
            + bottom_left_corner_area_m2
        )
        right_area_m2 = (
            (self.construction.frame_right.width * self.glazing_height_m)
            + top_right_corner_area_m2
            + bottom_right_corner_area_m2
        )

        top = self.construction.frame_top.u_value * top_area_m2
        bottom = self.construction.frame_bottom.u_value * bottom_area_m2
        left = self.construction.frame_left.u_value * left_area_m2
        right = self.construction.frame_right.u_value * right_area_m2

        return top + bottom + left + right

    @cached_property
    def total_psi_glazing_heat_flow(self) -> float:
        """The total Psi-Glazing-Edge heat flow (W/K) of the Aperture."""
        top = self.construction.frame_top.psi_glazing * self.glazing_width_m
        bottom = self.construction.frame_bottom.psi_glazing * self.glazing_width_m
        left = self.construction.frame_left.psi_glazing * self.glazing_height_m
        right = self.construction.frame_right.psi_glazing * self.glazing_height_m
        return top + bottom + left + right

    @cached_property
    def total_psi_install_heat_flow(self) -> float:
        """The total Psi-Install heat flow (W/K) of the Aperture."""
        top = self.construction.frame_top.psi_install * self.width_m
        bottom = self.construction.frame_bottom.psi_install * self.width_m
        left = self.construction.frame_left.psi_install * self.height_m
        right = self.construction.frame_right.psi_install * self.height_m
        return top + bottom + left + right

    @cached_property
    def u_value_wm2k(self) -> float:
        """The U-w-Value of the Aperture, as per ISO 10077.

        This value is impacted by thew window size, the glass, frame, Psi-Glazing-Edge, and Psi-Install.
        """
        try:
            return (
                self.total_glazing_heat_flow
                + self.total_frame_heat_flow
                + self.total_psi_glazing_heat_flow
                + self.total_psi_install_heat_flow
            ) / self.area_m2
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def g_value(self) -> float:
        """The g-value of the Aperture, as per EN410.

        This value is Center-of-Glass (CoG) and therefore does not include the
        impact of the frame (unlike NFRC's SHGC value).
        """
        return self.construction.glazing.g_value

    @cached_property
    def area_m2(self) -> float:
        """The total gross area of the Aperture (m2)."""
        return self.height_m * self.width_m

    @cached_property
    def net_area_m2(self) -> float:
        """The net area (less any children) of the surface (m2).
        For Apertures, this is the same as the gross area.
        """
        return self.area_m2

    @cached_property
    def glazing_height_m(self) -> float:
        """The glazing height of the Aperture (m)."""
        return self.height_m - (self.construction.frame_top.width + self.construction.frame_bottom.width)

    @cached_property
    def glazing_width_m(self) -> float:
        """The glazing width of the Aperture (m)."""
        return self.width_m - (self.construction.frame_left.width + self.construction.frame_right.width)

    @cached_property
    def frame_area_m2(self) -> float:
        """The total frame area of the Aperture (m2)."""
        return self.area_m2 - self.glazing_area_m2

    @cached_property
    def glazing_area_m2(self) -> float:
        """The total glazing area of the Aperture (m2)."""
        return self.glazing_width_m * self.glazing_height_m

    @cached_property
    def glazing_fraction(self) -> float:
        """The % (0.0-1.0) of the Aperture which is glazing (vs. frame)."""
        return self.glazing_area_m2 / self.area_m2

    @cached_property
    def frame_fraction(self) -> float:
        """The % (0.0-1.0) of the Aperture which is frame (vs. glazing)."""
        return self.frame_area_m2 / self.area_m2

    @cached_property
    def heat_loss_factor_W_K(self) -> float:
        """The UxA (net) value of the Aperture (W/K)."""
        return self.net_area_m2 * self.u_value_wm2k

    @cached_property
    def angle_from_horizontal(self) -> float:
        """The host-surface's angle (in degrees) from horizontal.
        (Up=0, Vertical-Surface=90, Down=180)
        """
        return self.host.angle_from_horizontal

    @cached_property
    def cardinal_orientation_angle(self) -> float:
        """The host-surface's cardinal orientation angle (in degrees) from North.
        (North=0, East=90, South=180, West=270)
        """
        return self.host.cardinal_orientation_angle

    @cached_property
    def cardinal_orientation_type(self) -> enums.CardinalOrientation:
        """The model.enums.CardinalOrientation (NORTH, EAST, SOUTH, WEST, HORIZONTAL) of the surface."""
        return self.host.cardinal_orientation_type

    @cached_property
    def cardinal_orientation_name(self) -> str:
        """The cardinal orientation name ("North", "South", "East", "West", "Horizontal") of the surface."""
        return self.host.cardinal_orientation_name
