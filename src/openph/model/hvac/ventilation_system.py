# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Fresh-Air Ventilation System and Devices."""

from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, ValuesView

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP

from openph.model.hvac.ventilation_device import PhEnVentilationDevice


class DeviceNotFoundError(Exception):
    def __init__(self, _device_ids, _search_id):
        self.msg = f"Device {_search_id} not Found. Valid device keys include only: {_device_ids}"
        super().__init__(self.msg)


# ----------------------------------------------------------------------------------------------------------------------
# -- Enums


class BasicVentEquipmentControl(Enum):
    NO_CONTROL = "No Control"
    TEMPERATURE_CONTROLLED = "Temperature Controlled"
    ENTHALPY_CONTROLLED = "Enthalpy Controlled"
    ALWAYS = "Always"


class AdditionalVentEquipmentControl(Enum):
    TEMPERATURE_CONTROLLED = "Temperature Controlled"
    HUMIDITY_CONTROLLED = "Humidity Controlled"


@dataclass(frozen=True)
class PhEnMechanicalSystemCollection:
    _devices: dict[str, PhEnVentilationDevice] = field(default_factory=dict)

    def add_new_mech_device(self, _key: str, _d: PhEnVentilationDevice) -> None:
        """Adds a new PHPP Mechanical 'device' to the collection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new mechanical device
            * _device (_base.PhxMechanicalDevice): The new PHPP mechanical device to
                add to the collection.

        Returns:
        --------
            * None
        """
        self._devices[_key] = _d

    @property
    def devices(self) -> ValuesView[PhEnVentilationDevice]:
        """Return a list of the devices in the collection."""
        return self._devices.values()

    def get_device_by_key(self, _id_number: str) -> PhEnVentilationDevice:
        """Return the PhEnVentilationDevice with the specified id-number from the collection."""
        try:
            return self._devices[_id_number]
        except KeyError:
            raise DeviceNotFoundError(list(self._devices.keys()), _id_number)


# ----------------------------------------------------------------------------------------------------------------------
# -- Seasonal System config and Attributes


@dataclass(frozen=True)
class PhEnVentilationSystemWinter:
    phpp: "PhEnPHPP"

    @cached_property
    def vent_system_ach(self) -> float:
        """

        PHPP V10 | Ventilation | J32

        =IF(K14="x",R79,L52)
        L52==IF($K$15="x",IF(LEFT(Ventilation!$K$12,1)="2",IF(AND(M8>0,K52>0),K52/M8,0),IF(AND(M8>0,J52>0),J52/M8,0)),"")

        Returns:
            The heating-period annual average ventilation air-flow rate in m3/h
        """
        return self.phpp.rooms.average_annual_airflow_ach


@dataclass(frozen=True)
class PhEnVentilationSystemSummer:
    phpp: "PhEnPHPP"

    basic_vent_equipment_control: BasicVentEquipmentControl = BasicVentEquipmentControl.ALWAYS
    additional_vent_equipment_control: AdditionalVentEquipmentControl = (
        AdditionalVentEquipmentControl.TEMPERATURE_CONTROLLED
    )
    _air_change_rate_basic_mech: float | None = None
    _additional_extract_system_daytime_ach: float | None = None
    _window_daytime_ach: float | None = None
    _window_nighttime_ach: float | None = None
    _additional_extract_system_nighttime_ach: float | None = None
    temperature_increase: float = 0.0  # K # TODO: This calculate this =SummVent!O57 Is this a bug in PHPP?

    # ------------------------------------------------------------------------------------------------------------------
    # -- Ventilation Inputs: PHPP V10 | SummVent K6:S26

    @cached_property
    def air_change_rate_basic_mech(self) -> float:
        """
        PHPP V10 | SummVent | L14

        Units: ACH
        """
        default = self.phpp.hvac.ventilation_system.winter.vent_system_ach
        return self._air_change_rate_basic_mech or default

    @property
    def additional_extract_system_daytime_ach(self) -> float:
        """
        PHPP V10 | SummVent | L21

        Units: ACH
        """
        default = 0.0
        return self._additional_extract_system_daytime_ach or default

    @property
    def window_daytime_ach(self) -> float:
        """
        PHPP V10 | SummVent | L25

        Units: ACH
        """
        default = self.air_change_rate_basic_mech * 0.25
        return self._window_daytime_ach or default

    @property
    def window_nighttime_ach(self) -> float:
        """
        PHPP V10 | SummVent | O53

        Units: ACH
        """
        default = self.window_daytime_ach * 0.5
        return self._window_nighttime_ach or default

    @property
    def additional_extract_system_nighttime_ach(self) -> float:
        """
        PHPP V10 | SummVent | O55

        Units: ACH
        """
        default = 0.0
        return self._additional_extract_system_nighttime_ach or default

    @property
    def vent_system_heat_recovery_efficiency(self) -> float:
        """

        PHPP V10 | SummVent | R8

        =IF(AND(COUNTIF(Cooling!T84:AE84,">"&Cooling!T8)>=2,ISNUMBER(Ventilation!N34)),Ventilation!N34,IF(ISNUMBER(Ventilation!L32),Ventilation!L32,0))

        Units: %
        """
        # TODO: Handle the 'cooling' case
        return self.phpp.hvac.ventilation_system.effective_heat_recovery

    @property
    def vent_system_subsoil_heat_recovery_efficiency(self) -> float:
        """

        PHPP V10 | SummVent | R9

        =Ventilation!Q34

        Units: %
        """
        # TODO: Calc the Subsoil SHX value correctly
        return 0.0

    # ------------------------------------------------------------------------------------------------------------------
    # -- Ventilation Effective Air-Change Rates: PHPP V10 | SummVent K28:S35

    @property
    def ventilation_ach_air_with_heat_recovery(self) -> float:
        """

        PHPP V10 | SummVent | R31

        =L31*(1-N31)*(1-P31)

        Units: ACH
        """
        return (
            self.air_change_rate_basic_mech
            * (1 - self.vent_system_subsoil_heat_recovery_efficiency)
            * (1 - self.vent_system_heat_recovery_efficiency)
        )

    @property
    def ventilation_ach_air_without_heat_recovery(self) -> float:
        """

        PHPP V10 | SummVent | R32

        =L32*(1-N32)

        Units: ACH
        """
        return self.air_change_rate_basic_mech * (1 - self.vent_system_subsoil_heat_recovery_efficiency)

    @property
    def ventilation_ach_ground_with_heat_recovery(self) -> float:
        """

        PHPP V10 | SummVent | R33

        =L33*N33*(1-P33)

        Units: ACH
        """
        return (
            self.air_change_rate_basic_mech
            * self.vent_system_subsoil_heat_recovery_efficiency
            * (1 - self.vent_system_heat_recovery_efficiency)
        )

    @property
    def ventilation_ach_ground_without_heat_recovery(self) -> float:
        """

        PHPP V10 | SummVent | R34

        =L34*N34

        Units: ACH
        """
        return self.air_change_rate_basic_mech * self.vent_system_subsoil_heat_recovery_efficiency

    @property
    def ventilation_ach_other(self) -> float:
        """

        PHPP V10 | SummVent | N43

        =L21+L25+IF(ISNUMBER(Ventilation!M27),Ventilation!M27,0)

        Units: ACH
        """
        return self.additional_extract_system_daytime_ach + self.window_daytime_ach + self.phpp.infiltration.n_v_res

    # ------------------------------------------------------------------------------------------------------------------
    # -- Ventilation Conductance Values: PHPP V10 | SummVent K36:S43

    @property
    def ventilation_conductance_air_with_heat_recovery_w_k(self) -> float:
        """

        PHPP V10 | SummVent | R39

        =IF(L39="","",L39*N39*P39)

        Units: W/K
        """
        return (
            self.phpp.rooms.total_ventilated_volume_m3
            * self.ventilation_ach_air_with_heat_recovery
            * self.phpp.constants.c_air
        )

    @property
    def ventilation_conductance_air_without_heat_recovery_w_k(self) -> float:
        """

        PHPP V10 | SummVent | R40

        =IF(L40="","",L40*N40*P40)

        Units: W/K
        """
        return (
            self.phpp.rooms.total_ventilated_volume_m3
            * self.ventilation_ach_air_without_heat_recovery
            * self.phpp.constants.c_air
        )

    @property
    def ventilation_conductance_ground_with_heat_recovery_w_k(self) -> float:
        """

        PHPP V10 | SummVent | R41

        =IF(L41="","",L41*N41*P41)

        Units: W/K
        """
        return (
            self.phpp.rooms.total_ventilated_volume_m3
            * self.ventilation_ach_ground_with_heat_recovery
            * self.phpp.constants.c_air
        )

    @property
    def ventilation_conductance_ground_without_heat_recovery_w_k(self) -> float:
        """

        PHPP V10 | SummVent | R42

        =IF(L42="","",L42*N42*P42)

        Units: W/K
        """
        return (
            self.phpp.rooms.total_ventilated_volume_m3
            * self.ventilation_ach_ground_without_heat_recovery
            * self.phpp.constants.c_air
        )

    @property
    def ventilation_conductance_other_w_k(self) -> float:
        """

        PHPP V10 | SummVent | R43

        =IF(L43="","",L43*N43*P43)

        Units: W/K
        """
        return self.phpp.rooms.total_ventilated_volume_m3 * self.ventilation_ach_other * self.phpp.constants.c_air


# ----------------------------------------------------------------------------------------------------------------------
# -- Controller


@dataclass
class PhEnVentilationSystem:
    phpp: "PhEnPHPP"

    device_collection: PhEnMechanicalSystemCollection = field(default_factory=PhEnMechanicalSystemCollection)
    winter: PhEnVentilationSystemWinter = field(init=False)
    summer: PhEnVentilationSystemSummer = field(init=False)

    def __post_init__(self):
        self.winter = PhEnVentilationSystemWinter(phpp=self.phpp)
        self.summer = PhEnVentilationSystemSummer(phpp=self.phpp)

    @cached_property
    def effective_supply_airflow_rate_m3_h(self) -> float:
        """The overall combined total Supply airflow rate (m3/hour) of all the Ventilation Devices

        PHPP V10 | Ventilation | J52

        =IF(K15="x",SUM(J47:J51),"")

        Units: %
        """
        return sum(d.total_supply_desing_airflow_m3_h for d in self.device_collection.devices)

    @cached_property
    def effective_exhaust_airflow_rate_m3_h(self) -> float:
        """The overall combined total Exhaust airflow rate (m3/hour) of all the Ventilation Devices

        PHPP V10 | Ventilation | K52

        =IF($K$15="x",SUM(K47:K51),"")
        ='Addl vent'!S24

        Units: %
        """
        return sum(d.total_exhaust_design_airflow_m3_h for d in self.device_collection.devices)

    @cached_property
    def effective_heat_recovery(self) -> float:
        """The overall combined total heat-recovery efficiency of all the Ventilation Devices

        PHPP V10 | Ventilation | L32

        =IF(K12="","",IF(K14="x",N100,M52))
        M52=IF($K$15="x",IF(LEFT(Ventilation!$K$12,1)="1",IF(SUM(J47:J51)>0,SUMPRODUCT(J47:J51,M47:M51)/SUM(J47:J51),""),""),"")

        Units: %
        """
        try:
            return (
                sum(
                    d.total_supply_desing_airflow_m3_h * d.effective_heat_recovery_efficiency
                    for d in self.device_collection.devices
                )
                / self.effective_supply_airflow_rate_m3_h
            )
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def effective_moisture_recovery(self) -> float:
        """The overall combined total moisture-recovery efficiency of all the Ventilation Devices

        PHPP V10 | Ventilation | M32

        =IF(K12="","",IF(K14="x",O91,N52))
        N52=IF($K$15="x",IF(LEFT(Ventilation!$K$12,1)="1",IF(SUM(J47:J51)>0,SUMPRODUCT(J47:J51,N47:N51)/SUM(J47:J51),""),""),"")

        Units: %
        """
        try:
            return (
                sum(
                    d.total_supply_desing_airflow_m3_h * d.effective_moisture_recovery_efficiency
                    for d in self.device_collection.devices
                )
                / self.effective_supply_airflow_rate_m3_h
            )
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def effective_subsoil_heat_recovery(self) -> float:
        """The overall combined total subsoil-heat-recovery efficiency of all the Ventilation Devices

        PHPP V10 | Ventilation | Q32

        =IF(OR(LEFT(K12,1)="2",LEFT(K12,1)="3",K12="",I32=0),0,IF(K14="x",N104,R52))
        R52=IF($K$15="x",IF(LEFT(Ventilation!$K$12,1)="1",IF(SUM(J47:J51)>0,SUMPRODUCT(J47:J51,R47:R51)/SUM(J47:J51),""),""),"")

        Units: %
        """
        try:
            return (
                sum(
                    d.total_supply_desing_airflow_m3_h * d.effective_subsoil_heat_recovery_efficiency
                    for d in self.device_collection.devices
                )
                / self.effective_supply_airflow_rate_m3_h
            )
        except ZeroDivisionError:
            return 0.0
