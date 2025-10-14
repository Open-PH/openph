# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PhEnPHPP Dataclasses for the: PHPP | Climate."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from math import atan, cos, exp, pi, sin
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP

from openph.model import enums


class PhEnHeatingDegreeHours:
    """Heating-Degree-Hours object for heating or cooling seasons.

    Kilo-Heating-Degree-Hours are the total seasonal delta-T (Kelvin) multiplied by the
    number of hours in the season.
    """

    def __init__(self, _period: PhEnClimateCalcPeriod, _int_temp: float) -> None:
        self.period = _period
        self.interior_temp = _int_temp

    @property
    def kilo_degree_hours_ambient_air(self) -> float:
        """The total seasonal kilo-heating-degree-hours (kKhr/period) to the ambient air."""
        return self.period.period_length_hours * (self.interior_temp - self.period.temperature_air_C) / 1000

    @property
    def kilo_degree_hours_sky(self) -> float:
        """The total seasonal kilo-heating-degree-hours (kKhr/period) to the sky."""
        return self.period.period_length_hours * (self.interior_temp - self.period.temperature_sky_C) / 1000


@dataclass
class PhEnClimateCalcPeriod:
    """A single annual-period (month) of the PHPP Climate worksheet."""

    # Required Arguments
    phpp: "PhEnPHPP"
    period_number: int

    # -- Props
    display_name: str = ""
    _period_length_hours: int = 1

    # -- Solar Radiation
    _radiation_north_kWh_m2: float = 0.0
    _radiation_east_kWh_m2: float = 0.0
    _radiation_south_kWh_m2: float = 0.0
    _radiation_west_kWh_m2: float = 0.0
    _radiation_horizontal_kWh_m2: float = 0.0

    # -- Temperatures
    _temperature_air_C: float = 0.0
    _temperature_sky_C: float = 0.0
    _temperature_dewpoint_C: float = 0.0
    _temperature_ground_C: float | None = 0.0

    # -- Radiation Factors
    GROUND_ALBEDO = 0.106  # PHPP-10 | Climate | E39 | Constant
    EXPONENT = 20  # PHPP-10 | Windows | FP2 | Constant
    RAD = pi / 180  # PHPP-10 | Windows | FR2 | Constant
    f_ground: float = 0.0

    # East-West Factors.
    # PHPP-10 | Areas | BX13:BX17 //// Windows | FN12:FY15
    f_EW_A0: float = 0.0
    f_EW_A1: float = 0.0
    f_EW_A2: float = 0.0
    f_EW_B1: float = 0.0

    # North-South Factors.
    # PHPP-10 | Areas | BX17:BX21 //// Windows | FN16:FY19
    f_NS_A0: float = 0.0
    f_NS_A1: float = 0.0
    f_NS_A2: float = 0.0
    f_alpha: float = 0.0
    f_cos_alpha: float = 0.0

    # Annual Procedure B2 Factor
    # PHPP-10 | Areas | BX41:CI140 //// Windows | FM23:FY174
    f_B2: float = 0.0

    def __post_init__(self) -> None:
        """Create the Heating-Degree-Hours objects for heating and cooling seasons."""
        self.heating = PhEnHeatingDegreeHours(self, self.phpp.set_points.min_interior_temp_C)
        self.cooling = PhEnHeatingDegreeHours(self, self.phpp.set_points.max_interior_temp_C)

    @property
    def period_length_hours(self) -> int:
        """Return the number of hours in the period.

        PHPP V10 | Cooling | AK107:AO107

        =$R107*AK$83

        Units: Number-of-Hours
        """
        return self._period_length_hours

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    @property
    def period_length_days(self) -> int:
        """Returns the number of days in the period.

        PHPP V10 | Climate | E24:P24

        Units: Number-Days
        """
        return int(self.period_length_hours / 24)

    @cached_property
    def outdoor_air_water_vapor_pressure_Pa(self):
        """PHPP V10 | Cooling | T131:AE131

        Water vapor pressure of outdoor air (Pa)
        =611 * EXP(0.000191275 + 0.07258 * T90 - 0.0002939 * T90^2 + 0.0000009841 * T90^3 - 0.00000000192 * T90^4)

        Units: Pa
        """
        return 611 * exp(
            0.000191275
            + 0.07258 * self.temperature_dewpoint_C
            - 0.0002939 * self.temperature_dewpoint_C**2
            + 0.0000009841 * self.temperature_dewpoint_C**3
            - 0.00000000192 * self.temperature_dewpoint_C**4
        )

    @cached_property
    def outdoor_air_absolute_humidity_kg_kg(self) -> float:
        """PHPP V10 | Cooling | T132:AE132

        The absolute humidity of outdoor air (kg/kg)
        =0.6222 * T131 / ( 101300 - T131)

        Units: kg/kg
        """
        return 0.6222 * self.outdoor_air_water_vapor_pressure_Pa / (101_300 - self.outdoor_air_water_vapor_pressure_Pa)

    @cached_property
    def share_of_maximum_losses_to_be_covered(self) -> float:
        """Anteil von max. Verlusten, der zu decken ist

        PHPP V10 | Climate | D42:P42

        =IF($X$25,IF(E26<10,1,IF(E26>16,0,0.000038*E26^4-0.0014*E26^3+0.0116*E26^2-0.032*E26+1)),0)

        Units: %
        """

        if self.phpp.climate.hemisphere == enums.Hemisphere.NORTH:
            if self.temperature_air_C < 10:
                return 1.0
            else:
                if self.temperature_air_C > 16:
                    return 0
                else:
                    return (
                        0.000038 * self.temperature_air_C**4
                        - 0.0014 * self.temperature_air_C**3
                        + 0.0116 * self.temperature_air_C**2
                        - 0.032 * self.temperature_air_C
                        + 1
                    )
        else:
            return 0.0

    @cached_property
    def h_t_factor(self) -> float:
        """HT-Faktor

        PHPP V10 | Climate | E43:P43

        =(0.78*E42+0.22)*E42

        Units: ?
        """
        return (0.78 * self.share_of_maximum_losses_to_be_covered + 0.22) * self.share_of_maximum_losses_to_be_covered

    # --- Basic Attributes

    @property
    def temperature_air_C(self) -> float:
        return self._temperature_air_C

    @temperature_air_C.setter
    def temperature_air_C(self, _input: float) -> None:
        self._temperature_air_C = _input

    @property
    def temperature_dewpoint_C(self) -> float:
        return self._temperature_dewpoint_C or 0.0

    @temperature_dewpoint_C.setter
    def temperature_dewpoint_C(self, _input: float) -> None:
        self._temperature_dewpoint_C = float(_input)

    @property
    def temperature_sky_C(self) -> float:
        return self._temperature_sky_C or 0.0

    @temperature_sky_C.setter
    def temperature_sky_C(self, _input: float) -> None:
        self._temperature_sky_C = float(_input)

    @property
    def temperature_ground_C(self) -> float:
        return self._temperature_ground_C or 0.0

    @temperature_ground_C.setter
    def temperature_ground_C(self, _input) -> None:
        self._temperature_ground_C = float(_input)

    # -- Radiation (kWh/m2) by Orientation
    # -- Note: these need to be properties so we can override them in the peak-month cooling calculations
    @property
    def radiation_north_kWh_m2(self) -> float:
        return self._radiation_north_kWh_m2

    @radiation_north_kWh_m2.setter
    def radiation_north_kWh_m2(self, _input: float) -> None:
        self._radiation_north_kWh_m2 = _input

    @property
    def radiation_east_kWh_m2(self) -> float:
        return self._radiation_east_kWh_m2

    @radiation_east_kWh_m2.setter
    def radiation_east_kWh_m2(self, _input: float) -> None:
        self._radiation_east_kWh_m2 = _input

    @property
    def radiation_south_kWh_m2(self) -> float:
        return self._radiation_south_kWh_m2

    @radiation_south_kWh_m2.setter
    def radiation_south_kWh_m2(self, _input: float) -> None:
        self._radiation_south_kWh_m2 = _input

    @property
    def radiation_west_kWh_m2(self) -> float:
        return self._radiation_west_kWh_m2

    @radiation_west_kWh_m2.setter
    def radiation_west_kWh_m2(self, _input: float) -> None:
        self._radiation_west_kWh_m2 = _input

    @property
    def radiation_horizontal_kWh_m2(self) -> float:
        return self._radiation_horizontal_kWh_m2

    @radiation_horizontal_kWh_m2.setter
    def radiation_horizontal_kWh_m2(self, _input: float) -> None:
        self._radiation_horizontal_kWh_m2 = _input

    def calculate_radiation_factors(self) -> None:
        """Calculate all of the required radiation-factors based on the attributes.
        Note that this method should be called after the radiation values have been setup.

        PHPP-10 V10 | Areas | BX11:CH21 //// Windows | FN11:FY19
        """

        # ---------------------------------------------------------------------
        # -- Calculate Ground Factor
        self.f_ground = self.GROUND_ALBEDO * self._radiation_horizontal_kWh_m2

        # ---------------------------------------------------------------------
        # -- Calculate Alpha factors
        if self._radiation_horizontal_kWh_m2 != 0:
            self.f_alpha = atan(
                (self._radiation_north_kWh_m2 - self._radiation_south_kWh_m2)
                / (self._radiation_horizontal_kWh_m2 - self.f_ground)
            )
        else:
            self.f_alpha = 0

        self.f_cos_alpha = cos(self.f_alpha) ** self.EXPONENT

        # ---------------------------------------------------------------------
        # Calculate East-West Factors
        self.f_EW_A0 = (self._radiation_horizontal_kWh_m2 + self.f_ground) / 4 + (
            self._radiation_west_kWh_m2 + self._radiation_east_kWh_m2
        ) / 4
        self.f_EW_A1 = (self._radiation_horizontal_kWh_m2 - self.f_ground) / 2
        self.f_EW_A2 = (self._radiation_horizontal_kWh_m2 + self.f_ground) / 4 - (
            self._radiation_west_kWh_m2 + self._radiation_east_kWh_m2
        ) / 4
        self.f_EW_B1 = (self._radiation_west_kWh_m2 - self._radiation_east_kWh_m2) / 2

        # ---------------------------------------------------------------------
        # Calculate North-South Factors
        a0 = 0.25 * (
            self._radiation_north_kWh_m2
            + self._radiation_south_kWh_m2
            + self._radiation_horizontal_kWh_m2
            + self.f_ground
        )
        self.f_NS_A0 = a0
        a1 = 0.5 * (self._radiation_horizontal_kWh_m2 - self.f_ground) / cos(self.f_alpha)
        self.f_NS_A1 = a1
        self.f_NS_A2 = (1 - self.f_cos_alpha) * 0.295 * a1 + self.f_cos_alpha * (
            a0 - 0.5 * (self._radiation_south_kWh_m2 + self._radiation_north_kWh_m2)
        )

        # ---------------------------------------------------------------------
        # -- Calculate B2 Factor
        if self.f_alpha == 0:
            self.f_B2 = 0
        else:
            self.f_B2 = (
                0.25
                * (
                    self._radiation_horizontal_kWh_m2
                    + self.f_ground
                    - self._radiation_south_kWh_m2
                    - self._radiation_north_kWh_m2
                )
                - self.f_NS_A2 * cos(2 * self.f_alpha)
            ) / sin(2 * self.f_alpha)

    def get_radiation_by_orientation(self, _orientation: enums.CardinalOrientation) -> float:
        """Return the climate period's radiation value (kWh/m2) for the given orientation."""
        mapping = {
            enums.CardinalOrientation.NORTH: self.radiation_north_kWh_m2,
            enums.CardinalOrientation.EAST: self.radiation_east_kWh_m2,
            enums.CardinalOrientation.SOUTH: self.radiation_south_kWh_m2,
            enums.CardinalOrientation.WEST: self.radiation_west_kWh_m2,
            enums.CardinalOrientation.HORIZONTAL: self.radiation_horizontal_kWh_m2,
        }
        return mapping[_orientation]


@dataclass
class PhEnClimatePeakHeatingLoad(PhEnClimateCalcPeriod):
    """One of the two Peak-Heating-Load calculation periods"""

    @property
    def temperature_dewpoint_C(self) -> float:
        """
        PHPP V10 | Climate | Q32:T32

        =IF($S$38,IF(S39,INDEX($EG$242:$EG$1473,MATCH($Z$18,$I$242:$I$1473,0)),MAX(E32:P32)+3),"")

        Units: C
        """
        if self._temperature_dewpoint_C:
            return self._temperature_dewpoint_C
        else:
            return max(self.phpp.climate.temperature_dewpoint_C) + 3

    @temperature_dewpoint_C.setter
    def temperature_dewpoint_C(self, _input) -> None:
        self._temperature_dewpoint_C = float(_input)

    @property
    def temperature_sky_C(self) -> float:
        """
        PHPP V10 | Climate | Q33:T33

        =IF($S$38,S50,"")

        S50=MIN(MAX(IF(ISNUMBER(S$32),-9.16+358.82*S$32/(241.2+S$32),0.0561*(S26+273.15)^1.5-273.15),S$26-25),S$26)

        Units: C
        """

        if self.temperature_dewpoint_C:
            a = -9.16 + 358.82 * self.temperature_dewpoint_C / (241.2 + self.temperature_dewpoint_C)
        else:
            a = 0.0561 * (self.temperature_air_C + 273.15) ** 1.5 - 273.15

        return min(max(a, self.temperature_air_C - 25), self.temperature_air_C)

    @temperature_sky_C.setter
    def temperature_sky_C(self, _input) -> None:
        self._temperature_sky_C = float(_input)

    @property
    def temperature_ground_C(self) -> float:
        """
        PHPP V10 | Climate | Q35:R35

        =IF(ISNUMBER($E26),Ground!$J$114,"")

        Units: C
        """
        return self.phpp.ground.peak_heat_load_design_ground_temp

    @temperature_ground_C.setter
    def temperature_ground_C(self, _input) -> None:
        self._temperature_ground_C = float(_input)


@dataclass
class PhEnClimatePeakCoolingLoad(PhEnClimateCalcPeriod):
    """One of the two Peak-Cooling-Load calculation periods."""

    @property
    def temperature_dewpoint_C(self) -> float:
        """
        PHPP V10 | Climate | Q32:T32

        =IF($S$38,IF(S39,INDEX($EG$242:$EG$1473,MATCH($Z$18,$I$242:$I$1473,0)),MAX(E32:P32)+3),"")

        Units: C
        """
        if self._temperature_dewpoint_C:
            return self._temperature_dewpoint_C
        else:
            return max(self.phpp.climate.temperature_dewpoint_C) + 3

    @temperature_dewpoint_C.setter
    def temperature_dewpoint_C(self, _input) -> None:
        self._temperature_dewpoint_C = float(_input)

    @property
    def temperature_sky_C(self) -> float:
        """
        PHPP V10 | Climate | Q33:T33

        =IF($S$38,S50,"")

        S50=MIN(MAX(IF(ISNUMBER(S$32),-9.16+358.82*S$32/(241.2+S$32),0.0561*(S26+273.15)^1.5-273.15),S$26-25),S$26)

        Units: C
        """
        if self.temperature_dewpoint_C:
            a = -9.16 + 358.82 * self.temperature_dewpoint_C / (241.2 + self.temperature_dewpoint_C)
        else:
            a = 0.0561 * (self.temperature_air_C + 273.15) ** 1.5 - 273.15

        return min(max(a, self.temperature_air_C - 25), self.temperature_air_C)

    @temperature_sky_C.setter
    def temperature_sky_C(self, _input) -> None:
        self._temperature_sky_C = float(_input)

    @property
    def temperature_ground_C(self) -> float:
        """
        PHPP V10 | Climate | S35:T35

        =IF(ISNUMBER($E26),Ground!$P$114,"")

        Units: C
        """
        if self._temperature_ground_C:
            return self._temperature_ground_C
        else:
            return self.phpp.ground.peak_cooling_load_design_ground_temp

    @temperature_ground_C.setter
    def temperature_ground_C(self, _input) -> None:
        self._temperature_ground_C = float(_input)


@dataclass
class PhEnClimate:
    """The PHPP Climate worksheet data with a collection of CalcPeriods (months)."""

    phpp: "PhEnPHPP"
    periods: list[PhEnClimateCalcPeriod] = field(default_factory=list)
    peak_heating_1: PhEnClimatePeakHeatingLoad = field(init=False)
    peak_heating_2: PhEnClimatePeakHeatingLoad = field(init=False)
    peak_cooling_1: PhEnClimatePeakCoolingLoad = field(init=False)
    peak_cooling_2: PhEnClimatePeakCoolingLoad = field(init=False)

    def __post_init__(self) -> None:
        self.peak_heating_1 = PhEnClimatePeakHeatingLoad(phpp=self.phpp, period_number=1)
        self.peak_heating_2 = PhEnClimatePeakHeatingLoad(phpp=self.phpp, period_number=1)
        self.peak_cooling_1 = PhEnClimatePeakCoolingLoad(phpp=self.phpp, period_number=1)
        self.peak_cooling_2 = PhEnClimatePeakCoolingLoad(phpp=self.phpp, period_number=1)

    hemisphere: enums.Hemisphere = enums.Hemisphere.NORTH  # TODO: Get hemisphere from the HB-model
    summer_daily_temperature_fluctuation: float = (
        8.0  # Climate!N25 # TODO: Get temp-fluctuation from the data... used for: Cooling!J34
    )

    @cached_property
    def latitude(self) -> float:
        """
        PHPP V10 | Climate |F25

        Units: Degrees
        """
        return 40.78  # TODO: Get from model. Build a 'Site' or 'Location'?

    @cached_property
    def number_of_periods(self) -> int:
        return len(self.periods)

    @cached_property
    def period_numbers(self) -> list[int]:
        """Return a list of the period-numbers, starting at 1."""
        return list(range(1, self.number_of_periods + 1))

    @cached_property
    def period_days(self) -> list[int]:
        """Returns a list with the number of days in each period.

        PHPP V10 | Climate | E24:P24

        Units: Number-Days
        """
        return [p.period_length_days for p in self.periods]

    @cached_property
    def radiation_north_kWh_m2(self) -> list[float]:
        return [p.radiation_north_kWh_m2 for p in self.periods]

    @cached_property
    def radiation_east_kWh_m2(self) -> list[float]:
        return [p.radiation_east_kWh_m2 for p in self.periods]

    @cached_property
    def radiation_south_kWh_m2(self) -> list[float]:
        return [p.radiation_south_kWh_m2 for p in self.periods]

    @cached_property
    def radiation_west_kWh_m2(self) -> list[float]:
        return [p.radiation_west_kWh_m2 for p in self.periods]

    @cached_property
    def radiation_global_kWh_m2(self) -> list[float]:
        return [p.radiation_horizontal_kWh_m2 for p in self.periods]

    @cached_property
    def temperature_air_C(self) -> list[float]:
        """

        PHPP V10 | Climate | E26:P26

        Units: C
        """
        return [p.temperature_air_C for p in self.periods]

    @cached_property
    def temperature_sky_C(self) -> list[float]:
        return [p.temperature_sky_C for p in self.periods]

    @cached_property
    def temperature_dewpoint_C(self) -> list[float]:
        return [p.temperature_dewpoint_C for p in self.periods]

    @cached_property
    def cooling_degree_hours_ambient_air(self) -> list[float]:
        """
        PHPP V10 | Cooling | T108:AE108

        =IF(Moni!AJ9,T$107*($R108-T84)/1000,T$107*(Moni!AK118-T84)/1000)

        Units: kKh
        """
        return [p.cooling.kilo_degree_hours_ambient_air for p in self.periods]

    @cached_property
    def cooling_degree_hours_sky_kKhr(self) -> list[float]:
        """

        PHPP V10 | Cooling | T109:AE109

        =IF(Moni!AJ9,T$107*($R$108-T91)/1000,T$107*(Moni!AK118-T91)/1000)

        Units: kKh
        """
        return [p.cooling.kilo_degree_hours_sky for p in self.periods]

    @cached_property
    def heating_degree_hours_ambient_air_kKhr(self) -> list[float]:
        """
        PHPP V10 | Heating | T97:AE97

        =IF(Moni!AJ9,T$96*($R98-T69)/1000,T$96*(Moni!$AK118-T69)/1000)

        Units: kKh
        """
        return [p.heating.kilo_degree_hours_ambient_air for p in self.periods]

    @cached_property
    def heating_degree_hours_sky_kKhr(self) -> list[float]:
        """
        PHPP V10 | Heating | T98:AE98

        =IF(Moni!AJ9,T$96*($R98-T75)/1000,T$96*(Moni!$AK118-T75)/1000)

        Units: kKh (kilodegree-hours)
        """
        return [p.heating.kilo_degree_hours_sky for p in self.periods]

    @cached_property
    def share_of_maximum_losses_to_be_covered(self) -> list[float]:
        """Anteil von max. Verlusten, der zu decken ist

        PHPP V10 | Climate | E42:P42

        Units: %
        """
        return [p.share_of_maximum_losses_to_be_covered for p in self.periods]

    @cached_property
    def h_t_factor(self) -> list[float]:
        """HT-Faktor

        PHPP V10 | Climate | E43:P43

        Units: ?
        """
        return [p.h_t_factor for p in self.periods]

    @cached_property
    def heating_period_days(self) -> float:
        """Heiztage

        PHPP V10 | Climate | AI26 (K9)

        =IF(ISNUMBER(AI27),MAX(0.1,SUMPRODUCT($E$43:$P$43,$E24:$P24)),"")

        Units: Days
        """
        return max(0.1, sum(a * b for a, b in zip(self.h_t_factor, self.period_days)))

    @cached_property
    def heating_degree_hours(self) -> float:
        """Gt

        PHPP V10 | Climate | AI27 (K10)

        =MAX(0.1,SUMPRODUCT($E$42:$P$42,20-$E$26:$P$26,$E$24:$P$24)*0.024)

        Units: Degree-C-Hours
        """
        return max(
            0.1,
            sum(
                a * (20 - b) * c
                for a, b, c in zip(self.share_of_maximum_losses_to_be_covered, self.temperature_air_C, self.period_days)
            )
            * 0.024,
        )

    @cached_property
    def heating_period_average_temperature_air_C(self) -> float:
        """Außentemp

        PHPP V10 | Climate | R42

        =IF(SUM($E$42:$P$42)>0,SUMPRODUCT($E$42:$P$42,$E$26:$P$26)/SUM($E$42:$P$42),AVERAGE($E$26:$P$26))

        Units: C
        """
        try:
            return sum(a * b for a, b in zip(self.share_of_maximum_losses_to_be_covered, self.temperature_air_C)) / sum(
                self.share_of_maximum_losses_to_be_covered
            )
        except ZeroDivisionError:
            return sum(self.temperature_air_C) / len(self.temperature_air_C)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Outdoor Air Additional Information (Zusatzinfo Außentemperatur)

    @cached_property
    def average_annual_air_temp_C(self) -> float:
        """Zusatzinfo Außentemperatur: Mittelwert

        PHPP V10 | Climate | AE29

        =AVERAGE(E26:P26)

        Units: C
        """
        try:
            return sum(self.temperature_air_C) / len(self.temperature_air_C)
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def ClimateAE30(self) -> float:
        """Zusatzinfo Außentemperatur: sin

        PHPP V10 | Climate | AE30

        =SIGN($F$25)*SUMPRODUCT($E26:$P26,SIN(($E23:$P23)*PI()/6))/6

        Units: ?
        """
        sign = (self.latitude > 0) - (self.latitude < 0)
        sum_product = sum(a * sin(b * pi / 6) for a, b in zip(self.temperature_air_C, self.period_numbers))
        return sign * sum_product / 6

    @cached_property
    def ClimateAE31(self) -> float:
        """Zusatzinfo Außentemperatur: cos

        PHPP V10 | Climate | AE31

        =SIGN($F$25)*SUMPRODUCT($E26:$P26,COS(($E23:$P23)*PI()/6))/6

        Units: ?
        """
        sign = (self.latitude > 0) - (self.latitude < 0)
        sum_product = sum(a * cos(b * pi / 6) for a, b in zip(self.temperature_air_C, self.period_numbers))
        return sign * sum_product / 6

    @cached_property
    def ClimateAE32(self) -> float:
        """Zusatzinfo Außentemperatur: Phase der Außentemp (für Erdreichblatt)

        PHPP V10 | Climate | AE32

        =ATAN(AE30/AE31)*6/PI()+IF(AE31>0,6)

        Units: ?
        """
        if self.ClimateAE31 > 0:
            a = 6
        else:
            a = 0
        return atan(self.ClimateAE30 / self.ClimateAE31) * 6 / pi + a
