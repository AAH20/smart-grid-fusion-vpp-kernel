"""
Smart Grid, Fusion Tokamak & VPP Core Engine.
Coordinates N-1 Security-Constrained OPF, 24-hour thermal/BESS unit commitment,
VPP dual-market arbitrage, Tokamak plasma MHD equilibrium, and real-time Dynamic Line Rating.
Zero external pip dependencies. Pure Python 3.10+.
"""

from __future__ import annotations
import datetime
import math
import random
import time
from typing import Dict, List, Tuple, Set, Optional

from smart_grid_fusion_vpp_kernel.core.models import (
    GeneratorNode,
    TransmissionBranch,
    SCOPFReport,
    BatteryStorageUnit,
    UnitCommitmentReport,
    DistributedEnergyResource,
    VPPCoOptimizationReport,
    PoloidalFieldCoil,
    TokamakEquilibriumReport,
    ConductorWeatherObservation,
    DLRScheduleReport,
    SmartGridBenchmarkReport,
)
from smart_grid_fusion_vpp_kernel.core.security_constrained_optimal_power_flow import (
    SecurityConstrainedOptimalPowerFlow,
)
from smart_grid_fusion_vpp_kernel.core.unit_commitment_thermal_battery import (
    UnitCommitmentThermalBatterySolver,
)
from smart_grid_fusion_vpp_kernel.core.virtual_power_plant_co_optimizer import (
    VirtualPowerPlantCoOptimizer,
)
from smart_grid_fusion_vpp_kernel.core.tokamak_plasma_mhd_equilibrium import (
    TokamakPlasmaMHDEquilibriumSolver,
)
from smart_grid_fusion_vpp_kernel.core.dynamic_line_rating_scheduler import (
    DynamicLineRatingScheduler,
)


class SmartGridFusionVPPEngine:
    """
    High-performance, pure-Python engine orchestrating energy grid optimization,
    magnetic fusion coil synthesis, and distributed virtual power plant trading.
    """

    def __init__(self):
        self.sc_opf_solver = SecurityConstrainedOptimalPowerFlow()
        self.uc_solver = UnitCommitmentThermalBatterySolver()
        self.vpp_optimizer = VirtualPowerPlantCoOptimizer()
        self.tokamak_solver = TokamakPlasmaMHDEquilibriumSolver()
        self.dlr_scheduler = DynamicLineRatingScheduler()

    @staticmethod
    def generate_synthetic_grid_scenario() -> Tuple[
        List[str],
        List[TransmissionBranch],
        List[GeneratorNode],
        Dict[str, float],
        List[BatteryStorageUnit],
        List[float],
        List[DistributedEnergyResource],
        List[PoloidalFieldCoil],
        ConductorWeatherObservation,
    ]:
        """
        Generates realistic transmission grid, 24-hr demand, VPP DER portfolio,
        fusion reactor PF coils, and microclimate telemetry.
        """
        # 1. 5-Bus Transmission Network with 6 Lines
        buses = ["bus_1", "bus_2", "bus_3", "bus_4", "bus_5"]
        branches = [
            TransmissionBranch("line_1_2", "bus_1", "bus_2", 0.05, 250.0, True),
            TransmissionBranch("line_1_3", "bus_1", "bus_3", 0.08, 180.0, True),
            TransmissionBranch("line_2_3", "bus_2", "bus_3", 0.04, 200.0, True),
            TransmissionBranch("line_2_4", "bus_2", "bus_4", 0.06, 220.0, True),
            TransmissionBranch("line_3_5", "bus_3", "bus_5", 0.07, 190.0, True),
            TransmissionBranch("line_4_5", "bus_4", "bus_5", 0.05, 230.0, True),
        ]

        # 2. Generators (Baseload Nuclear/CCGT, Peaker Turbines)
        generators = [
            GeneratorNode("gen_nuc_1", "bus_1", 100.0, 400.0, 18.5, 0.0008, 5.0, 8, 8, 2500.0),
            GeneratorNode("gen_ccgt_2", "bus_2", 50.0, 300.0, 28.0, 0.0012, 12.0, 4, 3, 1200.0),
            GeneratorNode("gen_peaker_4", "bus_4", 10.0, 150.0, 48.0, 0.0025, 25.0, 1, 1, 400.0),
            GeneratorNode("gen_peaker_5", "bus_5", 10.0, 120.0, 52.0, 0.0030, 20.0, 1, 1, 350.0),
        ]

        # 3. Base Demands across Buses (Total = 620 MW)
        bus_demands = {
            "bus_1": 40.0,
            "bus_2": 180.0,
            "bus_3": 150.0,
            "bus_4": 120.0,
            "bus_5": 130.0,
        }

        # 4. Battery Storage Unit
        batteries = [
            BatteryStorageUnit("bess_central_3", "bus_3", capacity_mwh=200.0, max_charge_mw=50.0, max_discharge_mw=50.0),
        ]

        # 5. 24-Hour Regional Load Profile (MW)
        hourly_demand_profile = [
            420.0, 390.0, 370.0, 360.0, 380.0, 430.0,
            520.0, 610.0, 680.0, 710.0, 720.0, 705.0,
            690.0, 685.0, 695.0, 715.0, 750.0, 780.0,
            760.0, 720.0, 660.0, 580.0, 510.0, 460.0,
        ]

        # 6. Distributed Energy Resources (VPP Portfolio)
        ders = [
            DistributedEnergyResource("vpp_solar_farm_1", "solar", 80.0, 65.0, 0.0, 2.0),
            DistributedEnergyResource("vpp_wind_park_2", "wind", 100.0, 75.0, 0.0, 4.0),
            DistributedEnergyResource("vpp_battery_pack_3", "battery", 50.0, 50.0, 8.0, 15.0),
            DistributedEnergyResource("vpp_ev_fleet_4", "battery", 30.0, 25.0, 12.0, 8.0),
            DistributedEnergyResource("vpp_industrial_load_5", "flexible_load", 20.0, 18.0, 22.0, 5.0),
        ]

        # 7. Tokamak Poloidal Field (PF) Coils (ITER-like arrangement around plasma vessel)
        coils = [
            PoloidalFieldCoil("pf_1_top_in", radius_r_m=1.8, height_z_m=2.8, max_current_ka=45.0, turns=150),
            PoloidalFieldCoil("pf_2_top_out", radius_r_m=4.5, height_z_m=2.4, max_current_ka=45.0, turns=150),
            PoloidalFieldCoil("pf_3_mid_out", radius_r_m=5.2, height_z_m=0.2, max_current_ka=40.0, turns=120),
            PoloidalFieldCoil("pf_4_bot_out", radius_r_m=4.6, height_z_m=-2.2, max_current_ka=45.0, turns=150),
            PoloidalFieldCoil("pf_5_divertor", radius_r_m=2.2, height_z_m=-2.9, max_current_ka=55.0, turns=180),
            PoloidalFieldCoil("pf_6_cs_central", radius_r_m=1.0, height_z_m=0.0, max_current_ka=60.0, turns=200),
        ]

        # 8. Microclimate Weather Telemetry for Dynamic Line Rating
        weather = ConductorWeatherObservation(
            ambient_temp_c=18.5,
            wind_speed_m_per_s=4.6,
            wind_angle_deg=65.0,
            solar_radiation_w_m2=750.0,
        )

        return (
            buses,
            branches,
            generators,
            bus_demands,
            batteries,
            hourly_demand_profile,
            ders,
            coils,
            weather,
        )

    def run_full_pipeline_benchmark(self) -> SmartGridBenchmarkReport:
        """
        Executes complete benchmark across all 5 smart grid & fusion optimization engines.
        """
        total_start = time.perf_counter()

        (
            buses,
            branches,
            generators,
            bus_demands,
            batteries,
            hourly_demands,
            ders,
            coils,
            weather,
        ) = self.generate_synthetic_grid_scenario()

        # 1. Security-Constrained Optimal Power Flow (SC-OPF)
        sc_report = self.sc_opf_solver.solve_sc_opf(buses, branches, generators, bus_demands)

        # 2. 24-Hour Thermal + BESS Unit Commitment
        uc_report = self.uc_solver.solve_commitment(generators, batteries, hourly_demands)

        # 3. Virtual Power Plant Dual-Market Co-Optimization
        vpp_report = self.vpp_optimizer.co_optimize(ders, wholesale_energy_price_mwh=42.0, regulation_clearing_price_mw=68.0)

        # 4. Tokamak Fusion Plasma MHD Equilibrium
        tokamak_report = self.tokamak_solver.solve_equilibrium(coils, plasma_current_ma=15.0)

        # 5. Real-Time Dynamic Line Rating (DLR)
        dlr_report = self.dlr_scheduler.calculate_rating(weather)

        total_elapsed_ms = (time.perf_counter() - total_start) * 1000.0

        return SmartGridBenchmarkReport(
            total_runtime_ms=round(total_elapsed_ms, 2),
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            sc_opf_summary={
                "total_cost_usd": sc_report.total_cost_usd,
                "contingencies_analyzed": float(sc_report.contingencies_analyzed),
                "violations_prevented": float(sc_report.contingency_violations_prevented),
                "mean_lmp_usd_mwh": round(sum(sc_report.marginal_locational_prices.values()) / max(1, len(sc_report.marginal_locational_prices)), 2),
                "latency_ms": sc_report.solver_latency_ms,
            },
            unit_commitment_summary={
                "operating_cost_usd": uc_report.total_operating_cost_usd,
                "startup_cost_usd": uc_report.startup_costs_usd,
                "unserved_energy_mwh": uc_report.unserved_energy_mwh,
                "latency_ms": uc_report.solver_latency_ms,
            },
            vpp_co_optimization_summary={
                "energy_revenue_usd": vpp_report.wholesale_arbitrage_revenue_usd,
                "regulation_revenue_usd": vpp_report.frequency_regulation_revenue_usd,
                "net_profit_usd": vpp_report.net_economic_profit_usd,
                "energy_committed_mw": vpp_report.energy_committed_mw,
                "reserves_committed_mw": vpp_report.ancillary_reserve_committed_mw,
                "latency_ms": vpp_report.solver_latency_ms,
            },
            tokamak_mhd_summary={
                "plasma_current_ma": tokamak_report.plasma_current_ma,
                "elongation_kappa": tokamak_report.elongation_kappa,
                "triangularity_delta": tokamak_report.triangularity_delta,
                "flux_residual": tokamak_report.poloidal_flux_residual,
                "h98_factor": tokamak_report.confinement_quality_factor,
                "latency_ms": tokamak_report.solver_latency_ms,
            },
            dlr_scheduling_summary={
                "static_rating_mw": dlr_report.static_line_rating_mw,
                "dynamic_rating_mw": dlr_report.dynamic_line_rating_mw,
                "headroom_gain_mw": dlr_report.headroom_gain_mw,
                "headroom_gain_pct": dlr_report.headroom_gain_pct,
                "core_temp_c": dlr_report.conductor_core_temp_c,
                "latency_us": dlr_report.solver_latency_us,
            },
        )
