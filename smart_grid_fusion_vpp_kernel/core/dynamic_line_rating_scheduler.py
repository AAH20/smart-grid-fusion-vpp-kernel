"""
Real-Time Dynamic Line Rating (DLR) Scheduler under IEEE Std 738 & CIGRE TB 601.
Computes overhead transmission conductor ampacity and thermal headroom based on
micro-climate weather data (cross-wind convective cooling, solar irradiance, ambient temperature).
Zero external pip dependencies. Pure Python 3.10+.
"""

from __future__ import annotations
import math
import time
from typing import List, Dict, Tuple, Set, Optional
from smart_grid_fusion_vpp_kernel.core.models import (
    ConductorWeatherObservation,
    DLRScheduleReport,
)


class DynamicLineRatingScheduler:
    """
    IEEE 738 steady-state conductor heat balance solver.
    Unlocks 20-50% hidden transmission capacity over conservative Static Line Ratings (SLR).
    """

    def __init__(
        self,
        conductor_diameter_m: float = 0.0281,  # ACSR Drake 795 kcmil
        conductor_resistance_25c_ohm_m: float = 7.28e-5,
        max_allowable_temp_c: float = 100.0,
        voltage_nominal_kv: float = 230.0,
        emissivity: float = 0.8,
        solar_absorptivity: float = 0.8,
    ):
        self.d = conductor_diameter_m
        self.r25 = conductor_resistance_25c_ohm_m
        self.t_max = max_allowable_temp_c
        self.v_kv = voltage_nominal_kv
        self.eps = emissivity
        self.alpha_s = solar_absorptivity
        self.alpha_temp = 0.0039  # Aluminium temp coeff of resistance (1/C)

    def _resistance_at_temp(self, t_c: float) -> float:
        return self.r25 * (1.0 + self.alpha_temp * (t_c - 25.0))

    def _compute_convective_cooling(
        self,
        t_cond: float,
        t_amb: float,
        wind_speed: float,
        wind_angle_deg: float,
    ) -> float:
        """IEEE 738 convective heat loss qc (W/m)."""
        t_film = (t_cond + t_amb) * 0.5
        # Air thermal properties at film temperature
        air_density = 1.293 - 1.52e-3 * t_film + 3.8e-6 * (t_film ** 2)
        air_viscosity = (1.458e-6 * ((t_film + 273.15) ** 1.5)) / (t_film + 273.15 + 110.4)
        air_conductivity = 2.424e-2 + 7.477e-5 * t_film - 4.407e-9 * (t_film ** 2)

        # Reynolds number
        re = (self.d * air_density * max(0.2, wind_speed)) / air_viscosity

        # Wind direction factor K_angle
        rad_ang = math.radians(wind_angle_deg)
        k_angle = 1.194 - math.cos(rad_ang) + 0.194 * math.cos(2.0 * rad_ang) + 0.368 * math.sin(2.0 * rad_ang)

        # Forced convection (low vs high wind speeds)
        qc1 = k_angle * (1.01 + 0.0372 * (re ** 0.52)) * air_conductivity * (t_cond - t_amb)
        qc2 = k_angle * (0.0119 * (re ** 0.6)) * air_conductivity * (t_cond - t_amb)
        forced_qc = max(qc1, qc2)

        # Natural convection (zero wind fallback)
        natural_qc = 0.0205 * (air_density ** 0.5) * (self.d ** 0.75) * ((max(0.0, t_cond - t_amb)) ** 1.25)

        return max(forced_qc, natural_qc)

    def _compute_radiative_cooling(self, t_cond: float, t_amb: float) -> float:
        """Stefan-Boltzmann radiation heat loss qr (W/m)."""
        tk_c = t_cond + 273.15
        tk_a = t_amb + 273.15
        return 17.8 * self.d * self.eps * (((tk_c / 100.0) ** 4) - ((tk_a / 100.0) ** 4))

    def _compute_solar_heating(self, solar_irradiance: float) -> float:
        """Solar heat gain qs (W/m)."""
        return self.alpha_s * solar_irradiance * self.d

    def calculate_rating(self, weather: ConductorWeatherObservation) -> DLRScheduleReport:
        """
        Calculates real-time Dynamic Line Rating (DLR) vs baseline Static Line Rating (SLR).
        """
        start_t = time.perf_counter()

        # 1. Conservative Baseline Static Line Rating (SLR)
        # Assumes T_amb = 40 C, Wind = 0.6 m/s @ 90 deg, Solar = 1000 W/m2
        slr_qc = self._compute_convective_cooling(self.t_max, 40.0, 0.6, 90.0)
        slr_qr = self._compute_radiative_cooling(self.t_max, 40.0)
        slr_qs = self._compute_solar_heating(1000.0)
        r_max = self._resistance_at_temp(self.t_max)

        slr_i_amps = math.sqrt(max(0.0, (slr_qc + slr_qr - slr_qs) / r_max))
        slr_mw = (math.sqrt(3.0) * self.v_kv * slr_i_amps) / 1000.0

        # 2. Real-Time Dynamic Line Rating (DLR)
        dlr_qc = self._compute_convective_cooling(
            self.t_max,
            weather.ambient_temp_c,
            weather.wind_speed_m_per_s,
            weather.wind_angle_deg,
        )
        dlr_qr = self._compute_radiative_cooling(self.t_max, weather.ambient_temp_c)
        dlr_qs = self._compute_solar_heating(weather.solar_radiation_w_m2)

        dlr_net_heat_dissipation = max(1.0, dlr_qc + dlr_qr - dlr_qs)
        dlr_i_amps = math.sqrt(dlr_net_heat_dissipation / r_max)
        dlr_mw = (math.sqrt(3.0) * self.v_kv * dlr_i_amps) / 1000.0

        headroom_mw = max(0.0, dlr_mw - slr_mw)
        headroom_pct = (headroom_mw / slr_mw * 100.0) if slr_mw > 0 else 0.0

        # Operating temperature at static rated current under actual weather
        curr_heat_gen = (slr_i_amps ** 2) * self._resistance_at_temp(weather.ambient_temp_c + 20.0)
        est_core_temp = weather.ambient_temp_c + (curr_heat_gen + dlr_qs) / max(1.0, (dlr_qc / max(1.0, self.t_max - weather.ambient_temp_c)))

        elapsed_us = (time.perf_counter() - start_t) * 1_000_000.0

        return DLRScheduleReport(
            static_line_rating_mw=round(slr_mw, 2),
            dynamic_line_rating_mw=round(dlr_mw, 2),
            headroom_gain_mw=round(headroom_mw, 2),
            headroom_gain_pct=round(headroom_pct, 2),
            conductor_core_temp_c=round(min(self.t_max, est_core_temp), 1),
            convective_cooling_w_m=round(dlr_qc, 2),
            radiative_cooling_w_m=round(dlr_qr, 2),
            solver_latency_us=round(elapsed_us, 2),
        )
