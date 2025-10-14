# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Dataclasses for the surfaces of: PHPP | Areas."""

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP

from openph.model.hvac.ventilation_device import PhEnVentilationDevice
from openph.model.programs.ventilation import PhEnProgramVentilation


@dataclass
class PhEnRoom:
    """A Single 'Room' (Space) within the PHPP Model."""

    identifier: str = field(init=False, default_factory=lambda: str(uuid.uuid4()))
    display_name: str = "_unnamed_space_"
    quantity: int = 1
    floor_area_m2: float = 0.0
    weighting_factor: float = 0.0
    net_volume_m3: float = 0.0

    # -- Ventilation Unit (ERV) serving the room
    vent_unit: None | PhEnVentilationDevice = None

    # -- Programs
    ventilation: PhEnProgramVentilation = field(default_factory=PhEnProgramVentilation)
    # occupancy: PhEnProgramOccupancy = field(default_factory=PhEnProgramOccupancy) # TODO: Implement Occupancy Program
    # lighting: PhEnProgramLighting = field(default_factory=PhEnProgramLighting) # TODO: Implement Lighting Program
    # elec_equip: PhEnProgramElecEquip = field(default_factory=PhEnProgramElecEquip) # TODO: Implement ElecEquip Program

    @cached_property
    def weighted_floor_area_m2(self) -> float:
        """Return the weighted floor area (TFA) of the room.

        Units: M2
        """
        return self.floor_area_m2 * self.weighting_factor

    @cached_property
    def clear_height_m(self) -> float:
        """Return the average height of the room (volume / area).

        Units: M
        """
        try:
            return self.net_volume_m3 / self.floor_area_m2
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def ventilated_volume_m3(self) -> float:
        """Return the ventilated volume of the room.

        Units: M3
        """
        STANDARD_RESIDENTIAL_ROOM_HEIGHT = 2.5  # m
        return self.floor_area_m2 * STANDARD_RESIDENTIAL_ROOM_HEIGHT

    @cached_property
    def ventilation_design_ach(self) -> float:
        """The design ventilation air-changes-hour for the room

        PHPP V10 | Addl Vent | M56:M85

        =IF(AND(ISNUMBER(I56),SUM(J56:L56)>0),MAX(J56:L56)/I56,"")

        Returns:
            The room's ventilation ACH at the design airflow rate.
        """
        try:
            return (
                max(
                    self.ventilation.load.supply_airflow_m3_h,
                    self.ventilation.load.exhaust_airflow_m3_h,
                    self.ventilation.load.transfer_airflow_m3_h,
                )
                / self.ventilated_volume_m3
            )
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def average_annual_supply_airflow_rate_m3_h(self) -> float:
        """
        mittlerer Volumenstrom in Betriebszeit
        PHPP V10 | Addl Vent | W56:W85

        =IF(AND(ISNUMBER(J56),ISNUMBER($AQ56),$D56>0),J56*$AQ56*$D56,"")

        Returns:
            The airflow in m3/h
        """
        return (
            self.ventilation.schedule.annual_average_reduction_factor
            * self.ventilation.load.supply_airflow_m3_h
            * self.quantity
        )

    @cached_property
    def average_annual_exhaust_airflow_rate_m3_h(self) -> float:
        """
        mittlerer Volumenstrom in Betriebszeit
        PHPP V10 | Addl Vent | X56:X85

        =IF(AND(ISNUMBER(K56),ISNUMBER($AQ56),$D56>0),K56*$AQ56*$D56,"")

        Returns:
            The airflow in m3/h
        """

        return (
            self.ventilation.schedule.annual_average_reduction_factor
            * self.ventilation.load.exhaust_airflow_m3_h
            * self.quantity
        )

    @cached_property
    def average_annual_transfer_airflow_rate_m3_h(self) -> float:
        """
        mittlerer Volumenstrom in Betriebszeit
        PHPP V10 | Addl Vent | Y56:Y85

        =IF(AND(ISNUMBER(L56),ISNUMBER($AQ56),$D56>0),L56*$AQ56*$D56,"")

        Returns:
            The airflow in m3/h
        """

        return (
            self.ventilation.schedule.annual_average_reduction_factor
            * self.ventilation.load.transfer_airflow_m3_h
            * self.quantity
        )

    @cached_property
    def average_annual_ach(self) -> float:
        """The average-annual ventilation air-changes-hour for the room

        PHPP V10 | Addl Vent | Z56:Z85

        =IF(SUM(W56:Y56)>0,MAX(W56:Y56)/AE56,"")

        Returns:
            The room's ventilation ACH at the annual average airflow rate.
        """
        try:
            return (
                max(
                    self.average_annual_supply_airflow_rate_m3_h,
                    self.average_annual_exhaust_airflow_rate_m3_h,
                    self.average_annual_transfer_airflow_rate_m3_h,
                )
                / self.ventilated_volume_m3
            )
        except ZeroDivisionError:
            return 0.0


@dataclass
class PhEnRooms:
    """Dataclass for the PHPP Rooms ("Addl vent" Worksheet)."""

    phpp: "PhEnPHPP"
    _rooms: dict[str, PhEnRoom] = field(default_factory=dict)

    def add_room(self, _room: PhEnRoom) -> None:
        """Add a room to the PHPP model."""
        self._rooms[_room.identifier] = _room

    @cached_property
    def rooms(self) -> list[PhEnRoom]:
        return list(self._rooms.values())

    @cached_property
    def rooms_by_ventilation_device(self) -> dict[int, list[PhEnRoom]]:
        rooms_by_device = defaultdict(list)
        for room in self.rooms:
            if room.vent_unit:
                rooms_by_device[room.vent_unit.id_num].append(room)
            else:
                rooms_by_device[None].append(room)
        return rooms_by_device

    @cached_property
    def total_floor_area_m2(self) -> float:
        """Return the total floor area of all rooms in the PHPP.

        Units: M2
        """
        return sum(_room.floor_area_m2 for _room in self._rooms.values())

    @cached_property
    def total_weighted_floor_area_m2(self) -> float:
        """Return the total weighted floor area (TFA) of all the rooms in the PHPP.

        Units: M2
        """
        return sum(_room.weighted_floor_area_m2 for _room in self._rooms.values())

    @cached_property
    def total_ventilated_volume_m3(self) -> float:
        """Return the total ventilated volume of all rooms in the PHPP.

        Units: M3
        """
        return sum(_room.ventilated_volume_m3 for _room in self._rooms.values())

    @cached_property
    def total_net_interior_volume_m3(self) -> float:
        """Return the total interior net volume (Vn50) of all rooms in the PHPP.

        Units: M3
        """
        return sum(_room.net_volume_m3 for _room in self._rooms.values())

    # --- Ventilation Airflow Rates

    def rooms_with_specified_ventilation_device(self, _vent_device_id: int) -> list[PhEnRoom]:
        """Return a list of Rooms which are served by the specified Ventilation Device."""
        return [r for r in self._rooms.values() if r.vent_unit and r.vent_unit.id_num == _vent_device_id]

    def total_supply_design_airflow_by_vent_id_m3_h(self, _vent_device_id: int) -> float:
        return sum(
            room.ventilation.load.supply_airflow_m3_h
            for room in self.rooms_with_specified_ventilation_device(_vent_device_id)
        )

    def total_exhaust_design_airflow_by_vent_id_m3_h(self, _vent_device_id: int) -> float:
        return sum(
            room.ventilation.load.exhaust_airflow_m3_h
            for room in self.rooms_with_specified_ventilation_device(_vent_device_id)
        )

    def annual_avg_airflow_rate_by_vent_id_m3_h(self, _vent_device_id: int) -> float:
        """The total annual average airflow rate (m3/h) for all rooms with the specified ventilation unit.

        PHPP V10 | Addl Vent | AH97:AH106

        =SUMIF($F$56:$F$85,$C97,AR$56:AR$85)

        Returns:
            Annual average airflow in m³/h
        """
        v_sups = sum(
            room.average_annual_supply_airflow_rate_m3_h
            for room in self.rooms_with_specified_ventilation_device(_vent_device_id)
        )
        v_eta = sum(
            room.average_annual_exhaust_airflow_rate_m3_h
            for room in self.rooms_with_specified_ventilation_device(_vent_device_id)
        )
        return max(v_sups, v_eta)

    @cached_property
    def total_average_annual_supply_airflow_rate_m3_h(self) -> float:
        """
        PHPP V10 | Ventilation | J52

        =IF($K$15="x",SUM(J47:J51),"")

        Returns:
            m3/h
        """
        return sum(room.average_annual_supply_airflow_rate_m3_h for room in self.rooms)

    @cached_property
    def total_average_annual_exhaust_airflow_rate_m3_h(self) -> float:
        """
        PHPP V10 | Ventilation | K52

        =IF($K$15="x",SUM(K47:K51),"")

        Returns:
            m3/h
        """
        return sum(room.average_annual_exhaust_airflow_rate_m3_h for room in self.rooms)

    @cached_property
    def average_annual_airflow_ach(self) -> float:
        """
        PHPP V10 | Ventilation | L52

        =IF($K$15="x",IF(LEFT(Ventilation!$K$12,1)="2",IF(AND(M8>0,K52>0),K52/M8,0),IF(AND(M8>0,J52>0),J52/M8,0)),"")

        Returns:
            ACH
        """
        try:
            airflow = (
                self.total_average_annual_supply_airflow_rate_m3_h
                or self.total_average_annual_exhaust_airflow_rate_m3_h
            )
            return airflow / self.total_ventilated_volume_m3
        except ZeroDivisionError:
            return 0.0
