# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Dataclasses for the surfaces of: PHPP | Areas."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Generic, TypeVar

from openph.model.enums import CardinalOrientation, ComponentExposureExterior, ComponentFaceType
from openph.model.envelope import PhEnApertureSurface, PhEnOpaqueSurface

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from phpp import PhEnPHPP

T = TypeVar("T", bound="PhEnOpaqueSurface | PhEnApertureSurface")


@dataclass
class PhEnEnvelopeSurfaceGroup(Generic[T]):
    """A Group of Surfaces with convenience methods for filtering and aggregating."""

    _surfaces: Sequence[T] = field(default_factory=list)

    def by_orientation(self, _orientation: CardinalOrientation) -> "PhEnEnvelopeSurfaceGroup":
        """Return a PhEnSurfaceGroup with all the surfaces that are facing a specific orientation.

        Args:
            _orientation (CardinalOrientation): The orientation to filter by.

        Returns:
            PhEnEnvelopeSurfaceGroup: A new group with only the filtered surfaces.
        """
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.cardinal_orientation_type == _orientation]
        )

    @cached_property
    def aperture_surfaces(self) -> "PhEnEnvelopeSurfaceGroup[PhEnApertureSurface]":
        """Return a PhEnSurfaceGroup with all the aperture surfaces in the group."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if isinstance(surface, PhEnApertureSurface)]
        )

    def __iter__(self) -> Iterator[T]:
        """Iterate over the surfaces in the group."""
        return iter(self._surfaces)

    @cached_property
    def above_grade(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are above grade."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.exposure_exterior == ComponentExposureExterior.EXTERIOR]
        )

    @cached_property
    def below_grade(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are below grade."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.exposure_exterior == ComponentExposureExterior.GROUND]
        )

    @cached_property
    def ua_value(self) -> float:
        """The total UxA value of the surfaces in the group (W/K)."""
        return sum(surface.heat_loss_factor_W_K for surface in self._surfaces)

    @cached_property
    def area_m2(self) -> float:
        """The total area of the surfaces in the group (m2)."""
        return sum(surface.net_area_m2 for surface in self._surfaces)

    @cached_property
    def average_u_value(self) -> float:
        """The average U-Value of the surfaces in the group (W/m2K)."""
        try:
            return self.ua_value / self.area_m2
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def north(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are facing North."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.cardinal_orientation_type == CardinalOrientation.NORTH]
        )

    @cached_property
    def east(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are facing East."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.cardinal_orientation_type == CardinalOrientation.EAST]
        )

    @cached_property
    def south(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are facing South."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.cardinal_orientation_type == CardinalOrientation.SOUTH]
        )

    @cached_property
    def west(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are facing West."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._surfaces if surface.cardinal_orientation_type == CardinalOrientation.WEST]
        )

    @cached_property
    def horizontal(self) -> "PhEnEnvelopeSurfaceGroup[T]":
        """Return a PhEnSurfaceGroup with all the surfaces that are horizontal."""
        return PhEnEnvelopeSurfaceGroup(
            [
                surface
                for surface in self._surfaces
                if surface.cardinal_orientation_type == CardinalOrientation.HORIZONTAL
            ]
        )

    @cached_property
    def winter_eff_heat_gain_surface_m2(self) -> float:
        """ "Return the total WINTER effective heat-gain-area [m2] of the surfaces in the
        group. This is NOT the solar-aperture-area (glazing), but rather the area used to
        calculate the heating-gain of the frame (for apertures), or the opaque area.
        """
        return sum(surface.heat_gain.winter.eff_heat_gain_area_m2 for surface in self._surfaces)

    @cached_property
    def winter_eff_solar_gain_area_m2(self) -> float:
        """Return the total WINTER effective solar-gain-area [m2] of the surfaces in the group.

        For apertures, this is equal to the glazing-area with all reduction factors applied.
        """
        return sum(surface.heat_gain.winter.eff_solar_gain_area_m2 for surface in self._surfaces)

    @cached_property
    def summer_eff_heat_gain_surface_m2(self) -> float:
        """ "Return the total SUMMER effective heat-gain-area [m2] of the surfaces in the
        group. This is NOT the solar-aperture-area (glazing), but rather the area used to
        calculate the heating-gain of the frame (for apertures), or the opaque area.
        """
        return sum(surface.heat_gain.summer.eff_heat_gain_area_m2 for surface in self._surfaces)

    @cached_property
    def summer_eff_solar_gain_area_m2(self) -> float:
        """Return the total SUMMER effective solar-gain-area [m2] of the surfaces in the group.

        For apertures, this is equal to the glazing-area with all the reduction factors applied.
        """
        return sum(surface.heat_gain.summer.eff_solar_gain_area_m2 for surface in self._surfaces)

    @cached_property
    def total_glazing_area_m2(self) -> float:
        """Return the total glazing area [m2] of the aperture surfaces in the group."""
        return sum(surface.glazing_area_m2 for surface in self.aperture_surfaces)


@dataclass
class PhEnAreas:
    """The Areas Tab of the PHPP with a collection of PhEnOpaqueSurfaces."""

    phpp: "PhEnPHPP"
    _opaque_surface_list: list[PhEnOpaqueSurface] = field(default_factory=list)

    @cached_property
    def floor_area_m2(self) -> float:
        """Return the total floor area (without any weighting factors) of all rooms in the PHPP."""
        return self.phpp.rooms.total_floor_area_m2

    @cached_property
    def weighted_floor_area_m2(self) -> float:
        """Return the total weighted floor area (TFA) of all the rooms in the PHPP."""
        return self.phpp.rooms.total_weighted_floor_area_m2

    @cached_property
    def all_surfaces(self) -> list[PhEnOpaqueSurface | PhEnApertureSurface]:
        """All the surfaces in the PHPP (Opaque + Apertures)"""
        return self._opaque_surface_list + [
            aperture for surface in self._opaque_surface_list for aperture in surface.apertures
        ]

    @cached_property
    def opaque_surfaces(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the opaque surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(self._opaque_surface_list)

    @cached_property
    def aperture_surfaces(self) -> PhEnEnvelopeSurfaceGroup[PhEnApertureSurface]:
        """All the aperture surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [aperture for surface in self._opaque_surface_list for aperture in surface.apertures]
        )

    @cached_property
    def aperture_orientations(self) -> list[CardinalOrientation]:
        """A list of all the orientations (North, South, East, West, Horizontal) of the aperture surfaces."""
        return [aperture.cardinal_orientation_type for aperture in self.aperture_surfaces]

    @cached_property
    def all_walls(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the wall surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._opaque_surface_list if surface.face_type == ComponentFaceType.WALL]
        )

    @cached_property
    def walls_to_ground(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the wall surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [
                surface
                for surface in self._opaque_surface_list
                if surface.face_type == ComponentFaceType.WALL
                and surface.exposure_exterior == ComponentExposureExterior.GROUND
            ]
        )

    @cached_property
    def all_roofs(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the roof surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._opaque_surface_list if surface.face_type == ComponentFaceType.ROOF_CEILING]
        )

    @cached_property
    def all_floors(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the floor surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [surface for surface in self._opaque_surface_list if surface.face_type == ComponentFaceType.FLOOR]
        )

    @cached_property
    def floors_to_ground(self) -> PhEnEnvelopeSurfaceGroup[PhEnOpaqueSurface]:
        """All the wall surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [
                surface
                for surface in self._opaque_surface_list
                if surface.face_type == ComponentFaceType.FLOOR
                and surface.exposure_exterior == ComponentExposureExterior.GROUND
            ]
        )

    @cached_property
    def windows(self) -> PhEnEnvelopeSurfaceGroup[PhEnApertureSurface]:
        """All the window surfaces in the PHPP."""
        return PhEnEnvelopeSurfaceGroup(
            [aperture for aperture in self.aperture_surfaces if aperture.face_type == ComponentFaceType.WINDOW]
        )

    @cached_property
    def envelop_conductance_to_ambient_air_W_K(self) -> float:
        """Sum of all the above-grade UxA (W/K) values."""
        return (
            self.all_walls.above_grade.ua_value
            + self.all_floors.above_grade.ua_value
            + self.all_roofs.above_grade.ua_value
            + self.windows.above_grade.ua_value
        )

    @cached_property
    def envelop_conductance_to_ground_W_K(self) -> float:
        """Sum of all the below-grade UxA (W/K) values."""

        # TODO: Add in thermal bridge ground loses (perim, BG)
        return (
            self.all_walls.below_grade.ua_value
            + self.all_floors.below_grade.ua_value
            + self.all_roofs.below_grade.ua_value
            + self.windows.below_grade.ua_value
        )

    @cached_property
    def envelope_convective_factor_W_K(self) -> float:
        """Sum of all the convective factors of all the opaque and window surfaces.

        PHPP V10 | Areas | BU35

        =SUM(BU41:BU141)+SUM(BU146:BU246)+Windows!JX20

        Units: W/K
        """
        return sum(s.heat_gain.winter.convective_factor_W_K for s in self.all_surfaces)
        # TODO: Add in the Thermal Bridge Convective Factor -> AREAS:BU35

    @cached_property
    def envelope_radiative_factor_W_K(self) -> float:
        """Sum of all the radiative factors of all the opaque and window surfaces.

        PHPP V10 | Areas | BT35

        Units: W/K
        """
        return sum(s.heat_gain.winter.radiative_factor_W_K for s in self.all_surfaces)
        # TODO: Add in the Thermal Bridge Radiative Factor -> AREAS:BT35

    @cached_property
    def specific_heat_capacity_Wh_m2K(self) -> float:
        """Specific Heat Capacity of the building in Wh/m2-K.

        PHPP V10 | Verification | K30
        """
        # TODO: Get Spec-Heat-Capacity from the HB-Model
        return 60.0

    @cached_property
    def heat_capacity_Wh_K(self):
        """Heat Capacity of the building in Wh/K.

        Units: Wh/K
        """
        return self.specific_heat_capacity_Wh_m2K * self.phpp.rooms.total_weighted_floor_area_m2

    @cached_property
    def walls_to_ground_area_m2(self) -> float:
        """Return the total net-area [m2] for all of the ground-contact walls."""
        return sum(w.net_area_m2 for w in self.walls_to_ground)

    @cached_property
    def floors_to_ground_area_m2(self) -> float:
        """Return the total net-area [m2] for all of the ground-contact walls."""
        return sum(w.net_area_m2 for w in self.floors_to_ground)

    # ------------------------------------------------------------------------------------------------------------------
    # -- SUMMARY Areas!AU6:AZ29

    @cached_property
    def total_walls_to_ground_heat_loss_factor_W_K(self) -> float:
        """External wall ground/basement

        PHPP V10 | Areas | AU16

        =SUMIF($BJ$35:$BJ$141,N16,$AU$35:$AU$141)

        Units: W/K
        """
        return sum(s.heat_loss_factor_W_K for s in self.walls_to_ground)

    @cached_property
    def total_floors_to_ground_heat_loss_factor_W_K(self) -> float:
        """Floor slab / basement ceiling

        PHPP V10 | Areas | AU18

        =SUMIF($BJ$35:$BJ$141,N18,$AU$35:$AU$141)

        Units: W/K
        """
        return sum(s.heat_loss_factor_W_K for s in self.floors_to_ground)

    @cached_property
    def total_perimeter_thermal_bridge_heat_loss_factor_W_K(self) -> float:
        """Perimeter thermal bridges

        PHPP V10 | Areas | AU24

        =SUMIF($BJ$146:$BJ$246,N24,$AU$146:$AU$246)

        Units: W/K
        """
        # TODO: implement TBs
        return 0.0

    @cached_property
    def total_below_grade_thermal_bridge_heat_loss_factor_W_K(self) -> float:
        """Thermal bridges FS/BC

        PHPP V10 | Areas | AU25

        =SUMIF($BJ$146:$BJ$246,N25,$AU$146:$AU$246)

        Units: W/K
        """
        # TODO: implement TBs
        return 0.0
