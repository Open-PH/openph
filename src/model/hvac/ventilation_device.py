# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Fresh-Air Ventilation System and Devices."""

from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from math import exp, log, pi
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from src.phpp import PhEnPHPP


# ----------------------------------------------------------------------------------------------------------------------
# -- Enums


class PhEnDuctType(Enum):
    SUPPLY = 1
    EXHAUST = 2


class PhEnDuctShape(Enum):
    RECTANGLE = "Rectangle"
    ROUND = "Round"


class PhEnVentilationDeviceInstallLocation(Enum):
    INSIDE = "Inside"
    OUTSIDE = "Outside"


# ----------------------------------------------------------------------------------------------------------------------
# -- Devices


@dataclass(frozen=True)
class PhEnDuct:
    device: "PhEnVentilationDevice"
    length_m: float = 1.0
    diameter_mm: float = 160
    height_mm: float = 0.0
    width_mm: float = 0.0
    insulation_thickness_mm: float = 25.4
    insulation_conductivity_w_mk: float = 0.04
    insulation_reflective: bool = True
    duct_type: PhEnDuctType = field(default=PhEnDuctType.SUPPLY)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Device Attributes

    @cached_property
    def koeff_1(self) -> float:
        """Temperature reduction coefficient 1 (Koeff1) - accounts for heat loss through supply duct
        walls with frost protection effects.

        This dimensionless coefficient (0-1) represents the fraction of temperature difference
        maintained after accounting for duct heat losses and frost protection system impacts.
        Lower values indicate greater heat loss through the duct system.

        PHPP V10 | Addl Vent | Q152
        Excel: =EXP(-SUMPRODUCT($M$127:$M$146,Q127:Q146,$AR$127:$AR$146)*Q$151)

        Returns:
            Dimensionless temperature retention factor (0-1)
        """
        return exp(-self.duct_coefficient * self.frost_protection_reduction_factor)

    @cached_property
    def koeff_2(self) -> float:
        """Temperature reduction coefficient 2 (Koeff2) - accounts for heat loss through exhaust duct walls.

        This dimensionless coefficient (0-1) represents the fraction of temperature difference
        maintained after accounting for duct heat losses. Used for exhaust air temperature calculations.

        PHPP V10 | Addl Vent | Q153
        Excel: =EXP(-SUMPRODUCT($N$127:$N$146,Q127:Q146,$AR$127:$AR$146))

        Returns:
            Dimensionless temperature retention factor (0-1)
        """
        return exp(-self.duct_coefficient)

    @cached_property
    def koeff_3(self) -> float:
        """Temperature reduction coefficient 3 (Koeff3) - accounts for heat loss through supply duct walls.

        This dimensionless coefficient (0-1) represents the fraction of temperature difference
        maintained after accounting for duct heat losses. Similar to koeff_1 but without frost
        protection factor.

        PHPP V10 | Addl Vent | Q154
        Excel: =EXP(-SUMPRODUCT($M$127:$M$146,Q127:Q146,$AR$127:$AR$146))

        Returns:
            Dimensionless temperature retention factor (0-1)
        """
        return exp(-self.duct_coefficient)

    @cached_property
    def frost_protection_reduction_factor(self) -> float:
        """Frost protection reduction factor (Reduktionsfaktor Frostschutz).

        Accounts for the impact of frost protection systems on heat recovery efficiency.
        Values less than 1.0 indicate efficiency reduction due to frost protection measures
        such as preheating or bypassing.

        PHPP V10 | Addnl Vent | AT97:AT106
        Excel: =IF(ISNUMBER(Y97),IF(Y97=0,IF(W97=Data!$C$298,0.97,1),0.8),1)

        Returns:
            Dimensionless reduction factor (0.8, 0.97, or 1.0)
        """
        if self.device.effective_subsoil_heat_recovery_efficiency == 0:
            if self.device.frost_protection_reqd:
                return 0.97
            else:
                return 1.0
        else:
            return 0.8

    # ------------------------------------------------------------------------------------------------------------------
    # -- Duct Attributes

    @cached_property
    def shape(self) -> PhEnDuctShape:
        """The cross-sectional shape of the duct (Rectangular or Round).

        Returns:
            PhEnDuctShape.RECTANGLE if height and width are specified, otherwise PhEnDuctShape.ROUND
        """
        if self.height_mm and self.width_mm:
            return PhEnDuctShape.RECTANGLE
        elif self.diameter_mm:
            return PhEnDuctShape.ROUND
        else:
            raise Exception("Error: Unknown duct-shape?")

    @cached_property
    def conductance_w_m_k(self) -> float:
        """Linear thermal transmittance (Y-value) of the insulated duct per unit length.

        This value represents the rate of heat transfer through the duct wall per unit length
        per degree temperature difference. It accounts for:
        - Convective heat transfer on the inner surface
        - Conduction through insulation
        - Convective heat transfer on the outer surface

        PHPP V10 | Addl Vent | K127:K146
        Excel: =IF(AND(ISNUMBER(BD127)),BD127,"")
               BD127=IF(ISNUMBER(BS127),PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BC127),"")

        Returns:
            Linear thermal transmittance in W/(m·K)
        """

        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_surface
        )

    @cached_property
    def heat_loss_coefficient_W_K(self) -> float:
        """Total heat loss coefficient for the entire duct length.

        This is the product of the linear thermal transmittance and the duct length,
        representing the total rate of heat loss per degree temperature difference.

        PHPP V10 | Addl Vent | AQ127:AQ146
        Excel: =D127*K127*L127

        Returns:
            Heat loss coefficient in W/K
        """
        return self.conductance_w_m_k * self.length_m

    @cached_property
    def duct_coefficient(self) -> float:
        """Dimensionless duct heat loss coefficient.

        This coefficient relates the duct heat loss to the air heat capacity flow rate.
        It's calculated by dividing the heat loss coefficient (W/K) by the volumetric heat
        capacity flow rate (m³/h x specific heat capacity of air).

        PHPP V10 | Addl Vent | AR127:AR146
        Excel: =IF(AND(ISNUMBER(AQ127),AS127>0),AQ127/(AS127*0.33),"")

        Returns:
            Dimensionless duct coefficient
        """
        return self.heat_loss_coefficient_W_K / (
            self.average_annual_airflow_rate_m3_h * self.device.phpp.constants.c_air
        )

    @cached_property
    def average_annual_airflow_rate_m3_h(self) -> float:
        """Average annual airflow rate through the duct during operation.

        This is the weighted average of airflow rates across all operating hours,
        calculated from room ventilation schedule.

        PHPP V10 | Addl Vent | AS127:AS146
        Excel: =IF(ISNUMBER(SUMPRODUCT($Q$123:$Z$123,$Q127:$Z127)),SUMPRODUCT($Q$123:$Z$123,$Q127:$Z127),"")

        Returns:
            Average airflow rate in m³/h
        """
        return self.device.average_annual_airflow_rate_m3_h

    @cached_property
    def duct_type_number(self) -> int:
        """Duct type classification number (Kanaltyp).

        Classifies ducts based on supply/exhaust type and relative flow rates:
        1 = Supply duct with supply > exhaust
        2 = Exhaust duct with supply > exhaust
        3 = Exhaust duct with exhaust >= supply
        4 = Supply duct with exhaust >= supply

        PHPP V10 | Addl Vent | AT127:AT146
        Excel: =IF(AND(ISNUMBER(SUMPRODUCT($Q$124:$Z$124,Q127:Z127)),
               ISNUMBER(SUMPRODUCT($Q$125:$Z$125,Q127:Z127)),SUM(M127:N127)=1),
               IF(SUMPRODUCT($Q$124:$Z$124,Q127:Z127)>SUMPRODUCT($Q$125:$Z$125,Q127:Z127),
               IF(M127=1,1,2),IF(N127=1,4,3)),"")

        Returns:
            Duct type number (1-4)
        """
        # TODO: Calculate duct_type_number
        return 1

    @cached_property
    def hydraulic_diameter_mm(self) -> float:
        """Hydraulic diameter for rectangular ducts (D_hydraulisch).

        For rectangular ducts, the hydraulic diameter is used in place of the circular
        diameter for heat transfer and pressure loss calculations. This is an intermediate
        calculation used when converting rectangular to equivalent circular dimensions.

        PHPP V10 | Addl Vent | AU127:AU146
        Excel: =2*(F127+G127)/PI()

        Returns:
            Hydraulic diameter in mm
        """
        return 2 * (self.width_mm + self.height_mm) / pi

    @cached_property
    def equivalent_diameter_mm(self) -> float:
        """Equivalent diameter for rectangular ducts (D_hydraulisch).

        Converts rectangular duct dimensions to an equivalent circular diameter for
        use in heat transfer calculations. Uses the hydraulic diameter formula:
        D_eq = 4 x Area / Perimeter

        PHPP V10 | Addl Vent | AV127:AV146
        Excel: =4*F127*G127/(2*F127+2*G127)

        Returns:
            Equivalent diameter in mm
        """
        try:
            return 4 * self.width_mm * self.height_mm / (2 * self.width_mm + 2 * self.height_mm)
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def outer_diameter_without_insulation_mm(self) -> float:
        """Outer diameter of the duct before insulation (Nennweite / Nominal Diameter).

        For round ducts, this is the specified diameter. For rectangular ducts,
        this uses the hydraulic diameter for heat transfer calculations.

        PHPP V10 | Addl Vent | AW127:AW146
        Excel: =IF(AND(ISNUMBER(AV127),E127=""),AU127,IF(AND(ISNUMBER(E127),SUM(F127:G127)=0),E127,""))

        Returns:
            Outer diameter without insulation in mm
        """
        if self.shape == PhEnDuctShape.RECTANGLE:
            return self.hydraulic_diameter_mm
        else:
            return self.diameter_mm

    @cached_property
    def nusselt_number_takeover(self) -> float:
        """Nusselt number for heat transfer calculations (Übernahme Nusselt / Takeover Nusselt).

        The Nusselt number is a dimensionless number that characterizes convective heat transfer.
        It represents the ratio of convective to conductive heat transfer. This value is
        calculated differently for round vs. rectangular ducts and is used to determine the
        convective heat transfer coefficient on the inner duct surface.

        PHPP translates "Nusselt" as "Nuts" but this refers to the Nusselt number, named
        after Wilhelm Nusselt, a pioneer in heat transfer research.

        PHPP V10 | Addl Vent | AX127:AX146
        Excel: =IF(AND(ISNUMBER(AV127),E127="",ISNUMBER(BW127)),BW127,
                  IF(AND(ISNUMBER(E127),SUM(F127:G127)=0,ISNUMBER(BZ127)),BZ127,""))

        Returns:
            Dimensionless Nusselt number
        """

        if self.shape == PhEnDuctShape.RECTANGLE:
            return self.nusselt_number_rectangular
        else:
            return self.nusselt_number_round

    @cached_property
    def temperature_difference_DJ(self) -> float:
        """Temperature difference (DJ / ΔT) driving heat transfer through duct walls.

        This is the temperature difference between the interior conditioned space and either:
        - The installation room temperature (for ducts in conditioned spaces, type > 2)
        - The exterior air temperature (for ducts in unconditioned spaces, type <= 2)

        This temperature difference drives the heat loss/gain calculations through the duct walls.

        PHPP V10 | Addl Vent | AY127:AY146
        Excel: =IF(AND(ISNUMBER(AT127),AT127>2),ABS($G$18-$F$116),ABS($G$18-$G$19))

        Returns:
            Temperature difference in Kelvin (K)
        """
        if self.duct_type_number > 2:
            return abs(self.device.phpp.set_points.min_interior_temp_C - self.device.installation_room_temp_C)
        else:
            return abs(
                self.device.phpp.set_points.min_interior_temp_C
                - self.device.phpp.climate.heating_period_average_temperature_air_C
            )

    @cached_property
    def outer_diameter_without_insulation_m(self) -> float:
        """Outer diameter of the duct before insulation in meters (Rohrdurchmesser außen).

        Converts the nominal diameter from millimeters to meters for use in heat transfer calculations.

        PHPP V10 | Addl Vent | AZ127:AZ146
        Excel: =AW127/1000

        Returns:
            Outer diameter without insulation in m
        """
        return self.outer_diameter_without_insulation_mm / 1000

    @cached_property
    def outer_diameter_with_insulation_m(self) -> float:
        """Outer diameter of the insulated duct in meters (Außendurchmesser).

        Includes the duct diameter plus twice the insulation thickness (both sides).
        Used in calculating the outer surface heat transfer coefficient.

        PHPP V10 | Addl Vent | BA127:BA146
        Excel: =(AW127+2*H127)/1000

        Returns:
            Outer diameter with insulation in m
        """
        return (self.outer_diameter_without_insulation_mm + 2 * self.insulation_thickness_mm) / 1000

    @cached_property
    def alpha_inside(self) -> float:
        """Convective heat transfer coefficient on the inner duct surface (α-innen / a-inside).

        This is the convective heat transfer coefficient (alpha) between the air flowing inside
        the duct and the inner duct wall surface. It's calculated from the Nusselt number and
        thermal conductivity of air:

        α = (Nu x λ_air) / D

        where Nu is the Nusselt number, λ_air is the thermal conductivity of air, and D is the
        characteristic length (diameter).

        PHPP V10 | Addl Vent | BB127:BB146
        Excel: =IF(AW127=0,0,AX127*24.915*0.001/(AW127*0.001))

        Note: 24.915 mW/(m·K) = thermal conductivity of air

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        try:
            return (
                self.nusselt_number_takeover
                * self.device.phpp.constants.thermal_conductivity_air
                * 1000  # Convert from W/(m·K) to W/(km·K)
                * 0.001  # Then back to W/(m·K)
                / (self.outer_diameter_without_insulation_mm * 0.001)
            )
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def alpha_surface(self) -> float:
        """Convective heat transfer coefficient on the outer duct surface (α-Oberfläche / a-surface).

        This is the convective heat transfer coefficient (alpha) between the outer duct surface
        (including insulation) and the surrounding air. It's calculated using natural convection
        correlations that depend on:
        - Surface temperature difference (drives buoyancy)
        - Surface emissivity (reflective vs. non-reflective insulation)
        - Surface orientation

        The correlation used is: α = factor x 4.8 + 1.62 x ΔT^(1/3)
        where factor = 0.1 for reflective surfaces, 0.85 for non-reflective surfaces.

        PHPP V10 | Addl Vent | BC127:BC146
        Excel: =IF(ISNUMBER(BR127),IF(J127="x",(0.1*4.8+1.62*BT127^0.333),(0.85*4.8+1.62*BT127^(0.333))),"")

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            factor = 0.1
        else:
            factor = 0.85

        return factor * 4.8 + 1.62 * self.surface_temperature_difference_iteration_5**0.333

    # ------------------------------------------------------------------------------------------------------------------
    # -- Iterative Solution for Surface Heat Transfer Coefficient
    #
    # The following properties solve for the outer surface heat transfer coefficient (alpha_surface)
    # using an iterative method. PHPP performs 5 iterations to converge on the correct value,
    # accounting for the coupling between surface temperature and convective heat transfer.
    #
    # Each iteration improves the estimate of:
    # - alpha_approximation_N: Surface heat transfer coefficient estimate
    # - thermal_transmittance_approximation_N: Overall duct thermal transmittance
    # - surface_temperature_difference_iteration_N: Temperature difference at outer surface
    #
    # The final iteration (5) provides the converged values used in the main calculations.

    # -- Iteration 1 (BF BG BH)

    @cached_property
    def alpha_approximation_iteration_1(self) -> float:
        """First iteration: Initial estimate of outer surface heat transfer coefficient (α-Näherung).

        Uses simple constant values based on insulation reflectivity as the starting point
        for the iterative solution:
        - 5.0 W/(m²·K) for reflective insulation
        - 8.0 W/(m²·K) for non-reflective insulation

        PHPP V10 | Addl Vent | BF127:BF146
        Excel: =IF(J127="x",5,8)

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            return 5.0
        else:
            return 8.0

    @cached_property
    def thermal_transmittance_approximation_iteration_1(self) -> float:
        """First iteration: Linear thermal transmittance estimate (k*-Näherung).

        Calculates the overall thermal transmittance per unit length using the first
        iteration's surface heat transfer coefficient estimate.

        PHPP V10 | Addl Vent | BG127:BG146
        Excel: =PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BF127)

        Returns:
            Linear thermal transmittance in W/(m·K)
        """
        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_approximation_iteration_1
        )

    @cached_property
    def surface_temperature_difference_iteration_1(self) -> float:
        """First iteration: Outer surface temperature difference estimate (OberflächentemperaturDiff_Näh).

        Calculates the temperature difference between ambient and the outer insulation surface
        based on the heat flow through the duct wall.

        PHPP V10 | Addl Vent | BH127:BH146
        Excel: =AY127-1/PI()*(1/(AW127*0.001*BB127)+CA127)*BG127*AY127

        Returns:
            Temperature difference in K
        """
        return (
            self.temperature_difference_DJ
            - 1
            / pi
            * (
                1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
                + self.insulation_thermal_resistance_per_m
            )
            * self.thermal_transmittance_approximation_iteration_1
            * self.temperature_difference_DJ
        )

    # -- Iteration 2 (BI BJ BK)

    @cached_property
    def alpha_approximation_iteration_2(self) -> float:
        """Second iteration: Improved outer surface heat transfer coefficient (α-Näherung).

        Refines the estimate using the natural convection correlation with the surface
        temperature difference from iteration 1.

        PHPP V10 | Addl Vent | BI127:BI146
        Excel: =IF(J127="x",(0.1*4.8+1.62*BH127^0.333),(0.85*4.8+1.62*BH127^(0.333)))

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            factor = 0.1
        else:
            factor = 0.85
        return factor * 4.8 + 1.62 * self.surface_temperature_difference_iteration_1**0.333

    @cached_property
    def thermal_transmittance_approximation_iteration_2(self) -> float:
        """Second iteration: Linear thermal transmittance estimate (k*-Näherung).

        PHPP V10 | Addl Vent | BJ127:BJ146
        Excel: =PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BI127)

        Returns:
            Linear thermal transmittance in W/(m·K)
        """
        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_approximation_iteration_2
        )

    @cached_property
    def surface_temperature_difference_iteration_2(self) -> float:
        """Second iteration: Outer surface temperature difference estimate (OberflächentemperaturDiff_Näh).

        PHPP V10 | Addl Vent | BK127:BK146
        Excel: =AY127-1/PI()*(1/(AW127*0.001*BB127)+CA127)*BJ127*AY127

        Returns:
            Temperature difference in K
        """
        return (
            self.temperature_difference_DJ
            - 1
            / pi
            * (
                1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
                + self.insulation_thermal_resistance_per_m
            )
            * self.thermal_transmittance_approximation_iteration_2
            * self.temperature_difference_DJ
        )

    # -- Iteration 3 (BL BM BN)

    @cached_property
    def alpha_approximation_iteration_3(self) -> float:
        """Third iteration: Outer surface heat transfer coefficient (α-Näherung).

        PHPP V10 | Addl Vent | BL127:BL146
        Excel: =IF(J127="x",(0.1*4.8+1.62*BK127^0.333),(0.85*4.8+1.62*BK127^(0.333)))

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            factor = 0.1
        else:
            factor = 0.85
        return factor * 4.8 + 1.62 * self.surface_temperature_difference_iteration_2**0.333

    @cached_property
    def thermal_transmittance_approximation_iteration_3(self) -> float:
        """Third iteration: Linear thermal transmittance estimate (k*-Näherung).

        PHPP V10 | Addl Vent | BM127:BM146
        Excel: =PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BL127)

        Returns:
            Linear thermal transmittance in W/(m·K)
        """
        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_approximation_iteration_3
        )

    @cached_property
    def surface_temperature_difference_iteration_3(self) -> float:
        """Third iteration: Outer surface temperature difference estimate (OberflächentemperaturDiff_Näh).

        PHPP V10 | Addl Vent | BN127:BN146
        Excel: =AY127-1/PI()*(1/(AW127*0.001*BB127)+CA127)*BM127*AY127

        Returns:
            Temperature difference in K
        """
        return (
            self.temperature_difference_DJ
            - 1
            / pi
            * (
                1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
                + self.insulation_thermal_resistance_per_m
            )
            * self.thermal_transmittance_approximation_iteration_3
            * self.temperature_difference_DJ
        )

    # -- Iteration 4 (BO BP BQ)

    @cached_property
    def alpha_approximation_iteration_4(self) -> float:
        """Fourth iteration: Outer surface heat transfer coefficient (α-Näherung).

        PHPP V10 | Addl Vent | BO127:BO146
        Excel: =IF(J127="x",(0.1*4.8+1.62*BN127^0.333),(0.85*4.8+1.62*BN127^(0.333)))

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            factor = 0.1
        else:
            factor = 0.85
        return factor * 4.8 + 1.62 * self.surface_temperature_difference_iteration_3**0.333

    @cached_property
    def thermal_transmittance_approximation_iteration_4(self) -> float:
        """Fourth iteration: Linear thermal transmittance estimate (k*-Näherung).

        PHPP V10 | Addl Vent | BP127:BP146
        Excel: =PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BO127)

        Returns:
            Linear thermal transmittance in W/(m·K)
        """
        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_approximation_iteration_4
        )

    @cached_property
    def surface_temperature_difference_iteration_4(self) -> float:
        """Fourth iteration: Outer surface temperature difference estimate (OberflächentemperaturDiff_Näh).

        PHPP V10 | Addl Vent | BQ127:BQ146
        Excel: =AY127-1/PI()*(1/(AW127*0.001*BB127)+CA127)*BP127*AY127

        Returns:
            Temperature difference in K
        """
        return (
            self.temperature_difference_DJ
            - 1
            / pi
            * (
                1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
                + self.insulation_thermal_resistance_per_m
            )
            * self.thermal_transmittance_approximation_iteration_4
            * self.temperature_difference_DJ
        )

    # -- Iteration 5 (BR BS BT) - FINAL CONVERGED VALUES

    @cached_property
    def alpha_approximation_iteration_5(self) -> float:
        """Fifth and final iteration: Converged outer surface heat transfer coefficient (α-Näherung).

        This is the final converged value used in the main thermal conductance calculation.
        PHPP uses exactly 5 iterations without an explicit convergence check.

        PHPP V10 | Addl Vent | BR127:BR146
        Excel: =IF(J127="x",(0.1*4.8+1.62*BQ127^0.333),(0.85*4.8+1.62*BQ127^(0.333)))

        Returns:
            Convective heat transfer coefficient in W/(m²·K)
        """
        if self.insulation_reflective:
            factor = 0.1
        else:
            factor = 0.85
        return factor * 4.8 + 1.62 * self.surface_temperature_difference_iteration_4**0.333

    @cached_property
    def thermal_transmittance_approximation_iteration_5(self) -> float:
        """Fifth and final iteration: Converged linear thermal transmittance (k*-Näherung).

        PHPP V10 | Addl Vent | BS127:BS146
        Excel: =PI()/(1/(AW127*0.001*BB127)+CA127+1/BA127/BR127)

        Returns:
            Linear thermal transmittance in W/(m·K)
        """
        return pi / (
            1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
            + self.insulation_thermal_resistance_per_m
            + 1 / self.outer_diameter_with_insulation_m / self.alpha_approximation_iteration_5
        )

    @cached_property
    def surface_temperature_difference_iteration_5(self) -> float:
        """Fifth and final iteration: Converged outer surface temperature difference (OberflächentemperaturDiff_Näh).

        This is the final converged surface temperature difference used in calculating
        the outer surface heat transfer coefficient (alpha_surface).

        PHPP V10 | Addl Vent | BT127:BT146
        Excel: =AY127-1/PI()*(1/(AW127*0.001*BB127)+CA127)*BS127*AY127

        Returns:
            Temperature difference in K
        """

        return (
            self.temperature_difference_DJ
            - 1
            / pi
            * (
                1 / (self.outer_diameter_without_insulation_mm * 0.001 * self.alpha_inside)
                + self.insulation_thermal_resistance_per_m
            )
            * self.thermal_transmittance_approximation_iteration_5
            * self.temperature_difference_DJ
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Reynolds Number and Nusselt Number Calculations
    #
    # These properties calculate dimensionless numbers used in heat transfer correlations.
    # The calculations differ for rectangular vs. round ducts.

    # -- For Rectangular Ducts

    @cached_property
    def air_velocity_rectangular_m_s(self) -> float:
        """Air velocity in rectangular ducts.

        Calculates the average air velocity through the rectangular duct cross-section.

        PHPP V10 | Addl Vent | BU127:BU146
        Excel: =AS127/(F127*0.001*G127*0.001)/3600

        Returns:
            Air velocity in m/s
        """
        try:
            return self.average_annual_airflow_rate_m3_h / (self.width_mm * 0.001 * self.height_mm * 0.001) / 3600
        except ZeroDivisionError:
            return 0.0

    @cached_property
    def reynolds_number_rectangular(self) -> float:
        """Reynolds number for rectangular ducts.

        Dimensionless number characterizing the flow regime (laminar vs. turbulent).
        Re = (velocity x characteristic_length) / kinematic_viscosity

        PHPP V10 | Addl Vent | BV127:BV146
        Excel: =BU127*AV127*0.001/0.00001384

        Returns:
            Dimensionless Reynolds number
        """
        return (
            self.air_velocity_rectangular_m_s
            * self.equivalent_diameter_mm
            * 0.001
            / self.device.phpp.constants.kinematic_viscosity_air
        )

    @cached_property
    def nusselt_number_rectangular(self) -> float:
        """Nusselt number for rectangular ducts.

        Dimensionless heat transfer coefficient for forced convection in turbulent flow.
        Uses the Dittus-Boelter correlation: Nu = 0.023 x Re^0.8 x Pr^0.4

        PHPP V10 | Addl Vent | BW127:BW146
        Excel: =0.023*BV127^0.8*0.71^0.4

        Returns:
            Dimensionless Nusselt number
        """
        return 0.023 * self.reynolds_number_rectangular**0.8 * self.device.phpp.constants.prandtl_number_air**0.4

    # -- For Round Ducts

    @cached_property
    def air_velocity_round_m_s(self) -> float:
        """Air velocity in round ducts.

        Calculates the average air velocity through the circular duct cross-section.

        PHPP V10 | Addl Vent | BX127:BX146
        Excel: =4*AS127/(((E127*0.001)^2*PI())*3600)

        Returns:
            Air velocity in m/s
        """
        return 4 * self.average_annual_airflow_rate_m3_h / (((self.diameter_mm * 0.001) ** 2 * pi) * 3600)

    @cached_property
    def reynolds_number_round(self) -> float:
        """Reynolds number for round ducts.

        Dimensionless number characterizing the flow regime (laminar vs. turbulent).
        Re = (velocity x diameter) / kinematic_viscosity

        PHPP V10 | Addl Vent | BY127:BY146
        Excel: =BX127*E127*0.001/0.00001384

        Returns:
            Dimensionless Reynolds number
        """
        return (
            self.air_velocity_round_m_s * self.diameter_mm * 0.001 / self.device.phpp.constants.kinematic_viscosity_air
        )

    @cached_property
    def nusselt_number_round(self) -> float:
        """Nusselt number for round ducts.

        Dimensionless heat transfer coefficient for forced convection in turbulent flow.
        Uses the Dittus-Boelter correlation: Nu = 0.023 x Re^0.8 x Pr^0.4

        PHPP V10 | Addl Vent | BZ127:BZ146
        Excel: =0.023*BY127^0.8*0.71^0.4

        Returns:
            Dimensionless Nusselt number
        """
        return 0.023 * self.reynolds_number_round**0.8 * self.device.phpp.constants.prandtl_number_air**0.4

    # ------------------------------------------------------------------------------------------------------------------
    # -- Insulation Thermal Resistance

    @cached_property
    def insulation_thermal_resistance_per_m(self) -> float:
        """Thermal resistance of the insulation layer per unit length (Hilf-R' / Auxiliary R-value).

        Calculates the radial thermal resistance of the cylindrical insulation layer.
        For a cylindrical shell, the thermal resistance per unit length is:

        R' = ln(r_outer/r_inner) / (2π x λ)

        where λ is the thermal conductivity of the insulation material.

        Returns 0 if there is no insulation (inner and outer diameters are equal).

        PHPP V10 | Addl Vent | CA127:CA146
        Excel: =IF(BA127=AZ127,0,1/2/I127*LN(BA127/AZ127))

        Returns:
            Thermal resistance per unit length in (m·K)/W
        """

        if self.outer_diameter_with_insulation_m == self.outer_diameter_without_insulation_m:
            return 0.0
        else:
            return (
                1
                / 2
                / self.insulation_conductivity_w_mk
                * log(self.outer_diameter_with_insulation_m / self.outer_diameter_without_insulation_m)
            )


@dataclass
class PhEnVentilationDeviceDucting:
    device: "PhEnVentilationDevice"
    supply_ducting: PhEnDuct = field(init=False)
    exhaust_ducting: PhEnDuct = field(init=False)

    def __post_init__(self):
        self.supply_ducting = PhEnDuct(device=self.device)
        self.exhaust_ducting = PhEnDuct(device=self.device)


@dataclass
class PhEnVentilationDevice:
    """PHPP Ventilation Device (HRV / ERV)."""

    phpp: "PhEnPHPP"

    id_num: int = 0
    display_name: str = "Ventilation Device"
    quantity: int = 1
    sensible_heat_recovery_effic: float = 0.0
    latent_heat_recovery_effic: float = 0.0
    electric_efficiency_Wh_m3: float = 0.45
    frost_protection_reqd: bool = True
    temperature_C_below_defrost_used: float = -5.0
    install_location: PhEnVentilationDeviceInstallLocation = PhEnVentilationDeviceInstallLocation.INSIDE
    _installation_room_temp_C: float | None = None

    ducting: PhEnVentilationDeviceDucting = field(init=False)

    def __post_init__(self):
        self.ducting = PhEnVentilationDeviceDucting(device=self)

    @property
    def installation_room_temp_C(self) -> float:
        """Temperature of the room where the ventilation device is installed.

        If the device is installed in an unconditioned space (e.g., attic, basement, garage),
        this should be set to the expected temperature of that space. If not specified,
        defaults to the average exterior air temperature during the heating period.

        PHPP V10 | Addl Vent | F116
        Label: "Temperature of installation room"

        Returns:
            Temperature in °C
        """
        return self._installation_room_temp_C or self.phpp.climate.heating_period_average_temperature_air_C

    # ------------------------------------------------------------------------------------------------------------------
    # -- Calculated Properties

    @cached_property
    def electric_power_per_airflow_W_per_m3h(self) -> float:
        """Electrical power consumption per unit airflow (P_el).

        Converts the specific fan power (electric efficiency in Wh/m³) to power per airflow rate
        by dividing by the specific heat capacity of air. This value represents the electrical
        power consumed by fans per m³/h of airflow.

        The calculation accounts for the fact that electrical power heats the air stream,
        contributing to the overall heat recovery effectiveness.

        PHPP V10 | Addl Vent | AQ97:AQ106
        Excel: =J97/0.33

        Note: 0.33 Wh/(m³·K) is the volumetric heat capacity of air

        Returns:
            Electrical power per airflow in W/(m³/h) or equivalently K (temperature rise)
        """
        return self.electric_efficiency_Wh_m3 / self.phpp.constants.c_air

    @cached_property
    def supply_air_temperature_after_heat_recovery_C(self) -> float:
        """Supply air temperature after heat recovery and duct losses (T_zu').

        Calculates the final supply air temperature delivered to the building after accounting for:
        - Heat recovery from exhaust air
        - Heat loss/gain through supply ductwork
        - Heat loss/gain through exhaust ductwork (affects heat recovery)
        - Installation room temperature effects

        This temperature is used to calculate the effective heat recovery efficiency when
        the ventilation device is installed outside the thermal envelope.

        PHPP V10 | Addl Vent | Q158
        Excel: =$F$116+(Q155*($F$116+($G$18-$F$116)*Q153-$G$19)+$G$19-$F$116)*Q154

        Returns:
            Supply air temperature in °C
        """
        return (
            self.installation_room_temp_C
            + (
                self.sensible_heat_recovery_effic
                * (
                    self.installation_room_temp_C
                    + (self.phpp.set_points.min_interior_temp_C - self.installation_room_temp_C)
                    * self.ducting.exhaust_ducting.koeff_2
                    - self.phpp.climate.heating_period_average_temperature_air_C
                )
                + self.phpp.climate.heating_period_average_temperature_air_C
                - self.installation_room_temp_C
            )
            * self.ducting.supply_ducting.koeff_3
        )

    @cached_property
    def effective_heat_recovery_efficiency(self) -> float:
        """Effective sensible heat recovery efficiency accounting for duct losses and fan heat (η_HR,eff).

        This is the overall heat recovery effectiveness including:
        - Manufacturer's rated heat recovery efficiency
        - Heat losses/gains through supply and exhaust ductwork
        - Heat added by fan motors (converted to temperature rise)
        - Installation location effects (inside vs. outside thermal envelope)

        For devices installed inside the thermal envelope:
        η_eff = η_unit x koeff_1 x koeff_2 + P_el/ΔT x (1 - koeff_2)

        For devices installed outside the thermal envelope:
        η_eff = (T_supply - T_exterior) / (T_interior - T_exterior)

        The result is clamped between 0 and 1 (0-100%).

        PHPP V10 | Addl Vent | S97
        Excel: =IF(AND(ISNUMBER(AP97),ISNUMBER(AQ97),ISNUMBER(AR97),ISNUMBER(R97),BC97),
               IF(AND(P97<>"",Q97=""),MAX(0,MIN(1,R97*AP97*AQ97+AR97/($G$18-$G$19)*(1-AQ97))),
               IF(AND(P97="",Q97<>"",ISNUMBER($F$116)),MAX(0,MIN(1,(AS97-$G$19)/($G$18-$G$19))),"")),"")

        Returns:
            Effective heat recovery efficiency (0-1, dimensionless)
        """
        if self.install_location == PhEnVentilationDeviceInstallLocation.INSIDE:
            result = max(
                0.0,
                min(
                    1.0,
                    self.sensible_heat_recovery_effic
                    * self.ducting.supply_ducting.koeff_1
                    * self.ducting.exhaust_ducting.koeff_2
                    + self.electric_power_per_airflow_W_per_m3h
                    / (
                        self.phpp.set_points.min_interior_temp_C
                        - self.phpp.climate.heating_period_average_temperature_air_C
                    )
                    * (1 - self.ducting.exhaust_ducting.koeff_2),
                ),
            )
            return result
        elif (
            self.install_location == PhEnVentilationDeviceInstallLocation.OUTSIDE
            and self.installation_room_temp_C is not None
        ):
            return max(
                0.0,
                min(
                    1.0,
                    (
                        self.supply_air_temperature_after_heat_recovery_C
                        - self.phpp.climate.heating_period_average_temperature_air_C
                    )
                    / (
                        self.phpp.set_points.min_interior_temp_C
                        - self.phpp.climate.heating_period_average_temperature_air_C
                    ),
                ),
            )
        else:
            return 0.0

    @cached_property
    def effective_moisture_recovery_efficiency(self) -> float:
        """Effective latent heat (moisture) recovery efficiency (η_moisture,eff).

        For Energy Recovery Ventilators (ERV), this represents the effectiveness of
        moisture transfer between exhaust and supply air streams. For Heat Recovery
        Ventilators (HRV), this value is 0.

        This value is typically looked up from the Components database based on the
        equipment model, or defaults to 0 if not specified.

        PHPP V10 | Addl Vent | T97
        Excel: =IF($F97="","",IF(ISNUMBER(G97),IF(VLOOKUP(LEFT($F97,4)&"*",
               Components!$LQ$13:$MF$914,4,FALSE)<>"",
               VLOOKUP(LEFT($F97,4)&"*",Components!$LQ$13:$MF$914,4,FALSE),
               Data!$B$376),""))

        Returns:
            Effective moisture recovery efficiency (0-1, dimensionless)
        """
        return self.latent_heat_recovery_effic

    @cached_property
    def effective_subsoil_heat_recovery_efficiency(self) -> float:
        """Effective subsoil (ground) heat recovery efficiency (η_ground,eff).

        For systems with earth-to-air heat exchangers (ground tubes), this represents
        the effectiveness of preheating/precooling outdoor air through underground ducts
        before it enters the ventilation unit.

        Calculated as the temperature rise fraction:
        η_ground = (T_preheated - T_exterior) / (T_ground - T_exterior)

        PHPP V10 | Addl Vent | Y97
        Excel: =IF(AND(ISNUMBER($G$18),ISNUMBER($G$19),ISNUMBER($G$20),ISNUMBER(G97)),
               ($G$20-$G$19)/($G$18-$G$19)*X97,"")

        Returns:
            Effective ground heat recovery efficiency (0-1, dimensionless)
        """
        # TODO: Support subsoil/ground heat-recovery calculations
        return 0.0

    # ------------------------------------------------------------------------------------------------------------------
    # -- Airflow Rates From Rooms

    @cached_property
    def total_supply_desing_airflow_m3_h(self) -> float:
        """Total supply design (peak) airflow rate for this ventilation device.

        This is the combined supply airflow serving all rooms/zones assigned to this device,
        calculated from the room ventilation schedules and equipment assignments. Note that
        this values does *not* consider the schedule and is instead the 'peak' load value.

        PHPP V10 | Addl Vent | AU97:AU106

        Returns:
            Total supply airflow in m³/h
        """
        return self.phpp.rooms.total_supply_design_airflow_by_vent_id_m3_h(self.id_num)

    @cached_property
    def total_exhaust_design_airflow_m3_h(self) -> float:
        """Total exhaust design (peak) airflow rate for this ventilation device.

        This is the combined exhaust airflow from all rooms/zones assigned to this device,
        calculated from the room ventilation schedules and equipment assignments. Note that
        this values does *not* consider the schedule and is instead the 'peak' load value.

        PHPP V10 | Addl Vent | AU97:AU106

        Returns:
            Total exhaust airflow in m³/h
        """
        return self.phpp.rooms.total_exhaust_design_airflow_by_vent_id_m3_h(self.id_num)

    @cached_property
    def design_airflow_rate_m3_h(self) -> float:
        """The overall design (peak) airflow rate (max of supply and exhaust) for this device.

        This is the combined  airflow from all rooms/zones assigned to this device,
        calculated from the room ventilation schedules and equipment assignments. Note that
        this values does *not* consider the schedule and is instead the 'peak' load value.

        PHPP V10 | Addl Vent | G97:G106

        =IF(AND(D97>0,AD97>0,AE97>0,NOT(BB97)),MAX(AD97:AE97)/D97,"")

        Returns:
            Total design airflow in m³/h
        """
        return max(self.total_supply_desing_airflow_m3_h, self.total_exhaust_design_airflow_m3_h)

    @cached_property
    def average_annual_airflow_rate_m3_h(self) -> float:
        """Average annual airflow rate of the device in operation.

        This is the weighted average of airflow rates across all operating hours,
        considering the room's ventilation schedule of operation.

        PHPP V10 | Addl Vent | Q123:Z123

        =$AU$97
        AU97=IF(D97>0,MAX(SUMIF($F$56:$F$85,$C97,AR$56:AR$85)/D97,SUMIF($F$56:$F$85,$C97,AS$56:AS$85)/D97),0)

        Returns:
            Annual average airflow in m³/h
        """
        return self.phpp.rooms.annual_avg_airflow_rate_by_vent_id_m3_h(self.id_num)
