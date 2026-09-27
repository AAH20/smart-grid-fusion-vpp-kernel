"""
Command-line Interface for Smart Grid, Fusion Tokamak & VPP Kernel.
Pure Python standard library (argparse, json, sys, time).
"""

from __future__ import annotations
import argparse
import json
import sys
import time

from smart_grid_fusion_vpp_kernel.engine import SmartGridFusionVPPEngine


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="smart-grid-vpp-kernel",
        description="Smart Grid, Tokamak Fusion Plasma & VPP Algorithmic Optimization Kernel",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: benchmark-all
    bench_parser = subparsers.add_parser("benchmark-all", help="Execute complete suite benchmark across all 5 power/fusion solvers")
    bench_parser.add_argument("--json", action="store_true", help="Output pure JSON format")

    # Command: sc-opf
    opf_parser = subparsers.add_parser("sc-opf", help="Run N-1 Security-Constrained Optimal Power Flow")

    # Command: unit-commitment
    uc_parser = subparsers.add_parser("unit-commitment", help="Run 24-hour Unit Commitment with thermal & BESS storage")

    # Command: vpp-co-optimize
    vpp_parser = subparsers.add_parser("vpp-co-optimize", help="Run VPP energy arbitrage vs frequency regulation co-optimization")
    vpp_parser.add_argument("--energy-price", type=float, default=45.0, help="Wholesale energy price $/MWh")
    vpp_parser.add_argument("--reg-price", type=float, default=65.0, help="Frequency regulation price $/MW")

    # Command: tokamak-mhd
    tokamak_parser = subparsers.add_parser("tokamak-mhd", help="Run inverse Grad-Shafranov PF coil current equilibrium solver")
    tokamak_parser.add_argument("--plasma-current", type=float, default=15.0, help="Target plasma current in MA")

    # Command: dlr-rating
    dlr_parser = subparsers.add_parser("dlr-rating", help="Run IEEE 738 Dynamic Line Rating conductor thermal rating")
    dlr_parser.add_argument("--ambient-c", type=float, default=20.0, help="Ambient temperature C")
    dlr_parser.add_argument("--wind-speed", type=float, default=4.0, help="Crosswind speed m/s")

    args = parser.parse_args()
    engine = SmartGridFusionVPPEngine()

    if args.command == "benchmark-all" or args.command is None:
        report = engine.run_full_pipeline_benchmark()

        if getattr(args, "json", False):
            print(json.dumps(report.__dict__, indent=2))
            return 0

        print("=" * 76)
        print("   SMART GRID, FUSION TOKAMAK & VPP KERNEL BENCHMARK REPORT")
        print("=" * 76)
        print(f" Timestamp:                 {report.timestamp}")
        print(f" Total Suite Latency:       {report.total_runtime_ms:.2f} ms")
        print("-" * 76)
        print(" 1. Security-Constrained OPF (N-1 Contingency Analysis):")
        for k, v in report.sc_opf_summary.items():
            print(f"    - {k:<25}: {v}")
        print(" 2. 24-Hour Thermal & Battery Unit Commitment (UC-ED):")
        for k, v in report.unit_commitment_summary.items():
            print(f"    - {k:<25}: {v}")
        print(" 3. Virtual Power Plant Dual-Market Co-Optimization:")
        for k, v in report.vpp_co_optimization_summary.items():
            print(f"    - {k:<25}: {v}")
        print(" 4. Tokamak Fusion Plasma Grad-Shafranov Equilibrium:")
        for k, v in report.tokamak_mhd_summary.items():
            print(f"    - {k:<25}: {v}")
        print(" 5. Real-Time Dynamic Line Rating (IEEE 738 Conductor Ampacity):")
        for k, v in report.dlr_scheduling_summary.items():
            print(f"    - {k:<25}: {v}")
        print("=" * 76)
        return 0

    elif args.command == "sc-opf":
        buses, branches, gens, demands, _, _, _, _, _ = engine.generate_synthetic_grid_scenario()
        res = engine.sc_opf_solver.solve_sc_opf(buses, branches, gens, demands)
        print(f"SC-OPF: Total Cost: ${res.total_cost_usd:.2f} | Analyzed {res.contingencies_analyzed} N-1 contingencies | Mitigated {res.contingency_violations_prevented} violations in {res.solver_latency_ms:.2f} ms")
        print(f"Base Dispatch: {res.base_dispatch_mw}")
        print(f"LMPs ($/MWh): {res.marginal_locational_prices}")
        return 0

    elif args.command == "unit-commitment":
        _, _, gens, _, bess, hourly_d, _, _, _ = engine.generate_synthetic_grid_scenario()
        res = engine.uc_solver.solve_commitment(gens, bess, hourly_d)
        print(f"24-Hr UC: Total Op Cost: ${res.total_operating_cost_usd:.2f} | Startup: ${res.startup_costs_usd:.2f} | Unserved: {res.unserved_energy_mwh:.2f} MWh in {res.solver_latency_ms:.2f} ms")
        return 0

    elif args.command == "vpp-co-optimize":
        _, _, _, _, _, _, ders, _, _ = engine.generate_synthetic_grid_scenario()
        res = engine.vpp_optimizer.co_optimize(ders, args.energy_price, args.reg_price)
        print(f"VPP Co-Opt: Net Profit: ${res.net_economic_profit_usd:.2f} (Energy: ${res.wholesale_arbitrage_revenue_usd:.2f}, Reg: ${res.frequency_regulation_revenue_usd:.2f}) | Committed: {res.energy_committed_mw:.1f} MW energy, {res.ancillary_reserve_committed_mw:.1f} MW reg in {res.solver_latency_ms:.2f} ms")
        return 0

    elif args.command == "tokamak-mhd":
        _, _, _, _, _, _, _, coils, _ = engine.generate_synthetic_grid_scenario()
        res = engine.tokamak_solver.solve_equilibrium(coils, plasma_current_ma=args.plasma_current)
        print(f"Tokamak MHD: Ip = {res.plasma_current_ma:.1f} MA | Elongation kappa = {res.elongation_kappa:.2f} | Triangularity delta = {res.triangularity_delta:.2f} | Flux Res: {res.poloidal_flux_residual:.4f} in {res.solver_latency_ms:.2f} ms")
        print(f"PF Coil Currents (kA): {res.coil_currents_ka}")
        return 0

    elif args.command == "dlr-rating":
        from smart_grid_fusion_vpp_kernel.core.models import ConductorWeatherObservation
        w = ConductorWeatherObservation(args.ambient_c, args.wind_speed, 90.0, 800.0)
        res = engine.dlr_scheduler.calculate_rating(w)
        print(f"DLR: Static = {res.static_line_rating_mw:.1f} MW -> Dynamic = {res.dynamic_line_rating_mw:.1f} MW (+{res.headroom_gain_pct:.1f}% Headroom gain) | Conductor Core Temp: {res.conductor_core_temp_c:.1f} C in {res.solver_latency_us:.1f} us")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
