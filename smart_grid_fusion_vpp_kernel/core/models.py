"""
Data models and typed structures for Smart Grid, Fusion Tokamak & VPP Optimization Kernel.
Zero external pip dependencies. Strict Python 3.10+ typing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple


@dataclass(slots=True)
class GeneratorNode:
    gen_id: str
    bus_id: str
    p_min_mw: float
    p_max_mw: float
    marginal_cost_per_mwh: float
    quadratic_cost_coeff: float = 0.001
    ramp_rate_mw_per_min: float = 10.0
    min_up_time_hrs: int = 1
    min_down_time_hrs: int = 1
    startup_cost: float = 500.0


@dataclass(slots=True)
class TransmissionBranch:
    branch_id: str
    from_bus: str
    to_bus: str
    reactance_x: float  # p.u.
    thermal_limit_mw: float
    is_contingency_critical: bool = True


@dataclass(slots=True)
class SCOPFReport:
    total_cost_usd: float
    base_dispatch_mw: Dict[str, float]
    branch_flows_mw: Dict[str, float]
    contingencies_analyzed: int
    contingency_violations_prevented: int
    marginal_locational_prices: Dict[str, float]
    solver_latency_ms: float


@dataclass(slots=True)
class BatteryStorageUnit:
    bess_id: str
    bus_id: str
    capacity_mwh: float
    max_charge_mw: float
    max_discharge_mw: float
    roundtrip_efficiency: float = 0.90
    current_soc_mwh: float = 0.0
    degradation_cost_per_mwh: float = 15.0


@dataclass(slots=True)
class UnitCommitmentReport:
    total_operating_cost_usd: float
    startup_costs_usd: float
    committed_schedule: Dict[str, List[int]]  # gen_id -> binary 0/1 per hour
    hourly_generation_mw: Dict[str, List[float]]
    battery_dispatch_mw: Dict[str, List[float]]  # positive = discharge, negative = charge
    unserved_energy_mwh: float
    solver_latency_ms: float


@dataclass(slots=True)
class DistributedEnergyResource:
    der_id: str
    resource_type: str  # "solar", "wind", "battery", "flexible_load"
    capacity_mw: float
    forecasted_output_mw: float
    marginal_cost_per_mwh: float
    ancillary_ramp_rate_mw_s: float  # for fast frequency response


@dataclass(slots=True)
class VPPCoOptimizationReport:
    wholesale_arbitrage_revenue_usd: float
    frequency_regulation_revenue_usd: float
    battery_degradation_cost_usd: float
    net_economic_profit_usd: float
    energy_committed_mw: float
    ancillary_reserve_committed_mw: float
    der_allocations: Dict[str, Tuple[float, float]]  # der_id -> (energy_mw, reserve_mw)
    solver_latency_ms: float


@dataclass(slots=True)
class PoloidalFieldCoil:
    coil_id: str
    radius_r_m: float
    height_z_m: float
    max_current_ka: float
    turns: int = 100


@dataclass(slots=True)
class TokamakEquilibriumReport:
    plasma_current_ma: float
    coil_currents_ka: Dict[str, float]
    x_point_coordinates: Tuple[float, float]  # (R, Z) magnetic null in meters
    elongation_kappa: float
    triangularity_delta: float
    poloidal_flux_residual: float
    confinement_quality_factor: float
    solver_latency_ms: float


@dataclass(slots=True)
class ConductorWeatherObservation:
    ambient_temp_c: float
    wind_speed_m_per_s: float
    wind_angle_deg: float
    solar_radiation_w_m2: float


@dataclass(slots=True)
class DLRScheduleReport:
    static_line_rating_mw: float
    dynamic_line_rating_mw: float
    headroom_gain_mw: float
    headroom_gain_pct: float
    conductor_core_temp_c: float
    convective_cooling_w_m: float
    radiative_cooling_w_m: float
    solver_latency_us: float


@dataclass(slots=True)
class SmartGridBenchmarkReport:
    total_runtime_ms: float
    timestamp: str
    sc_opf_summary: Dict[str, float]
    unit_commitment_summary: Dict[str, float]
    vpp_co_optimization_summary: Dict[str, float]
    tokamak_mhd_summary: Dict[str, float]
    dlr_scheduling_summary: Dict[str, float]
