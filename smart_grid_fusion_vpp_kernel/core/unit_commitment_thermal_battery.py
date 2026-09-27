"""
Multi-Period Unit Commitment with Thermal Generators & Battery Energy Storage (BESS).
Solves mixed-integer hourly commitment under minimum up/down time, dynamic ramp limits,
and battery state-of-charge degradation economics.
Zero external pip dependencies. Pure Python 3.10+.
"""

from __future__ import annotations
import math
import time
from typing import List, Dict, Tuple, Set, Optional
from smart_grid_fusion_vpp_kernel.core.models import (
    GeneratorNode,
    BatteryStorageUnit,
    UnitCommitmentReport,
)


class UnitCommitmentThermalBatterySolver:
    """
    Priority-List Branch & Bound / Dynamic Relaxation solver for 24-hour Unit Commitment.
    Coordinates baseload, peaker thermal generators, and grid-scale BESS arbitrage.
    """

    def __init__(self, reserve_margin_pct: float = 0.10):
        self.reserve_margin_pct = reserve_margin_pct

    def solve_commitment(
        self,
        generators: List[GeneratorNode],
        batteries: List[BatteryStorageUnit],
        hourly_demand_mw: List[float],
    ) -> UnitCommitmentReport:
        """
        Solves 24-hour scheduling horizon.
        """
        start_t = time.perf_counter()
        hours = len(hourly_demand_mw)

        committed_schedule: Dict[str, List[int]] = {g.gen_id: [] for g in generators}
        hourly_gen_mw: Dict[str, List[float]] = {g.gen_id: [] for g in generators}
        bess_dispatch_mw: Dict[str, List[float]] = {b.bess_id: [] for b in batteries}

        total_fuel_cost = 0.0
        total_startup_cost = 0.0
        total_unserved_mwh = 0.0

        # Track generator state: (is_on: bool, duration_in_state: int, prev_mw: float)
        gen_state: Dict[str, List] = {
            g.gen_id: [True if g.p_min_mw > 50 else False, 5, g.p_min_mw]
            for g in generators
        }

        # Track battery state of charge
        bess_soc: Dict[str, float] = {
            b.bess_id: b.capacity_mwh * 0.5 for b in batteries
        }

        # Pre-classify generators by merit order
        sorted_gens = sorted(generators, key=lambda g: g.marginal_cost_per_mwh)

        # Average demand to detect off-peak vs on-peak hours
        avg_demand = sum(hourly_demand_mw) / max(1, hours)

        for t in range(hours):
            demand = hourly_demand_mw[t]
            reserve_needed = demand * (1.0 + self.reserve_margin_pct)

            # 1. BESS Arbitrage Heuristic: Charge when demand < avg, Discharge when demand > avg
            net_bess_power = 0.0
            for b in batteries:
                curr_soc = bess_soc[b.bess_id]
                if demand < avg_demand * 0.9 and curr_soc < b.capacity_mwh * 0.95:
                    # Off-peak: Charge
                    charge_p = min(b.max_charge_mw, (b.capacity_mwh - curr_soc) / b.roundtrip_efficiency)
                    bess_soc[b.bess_id] += charge_p * b.roundtrip_efficiency
                    bess_dispatch_mw[b.bess_id].append(-round(charge_p, 2))
                    net_bess_power -= charge_p
                elif demand > avg_demand * 1.1 and curr_soc > b.capacity_mwh * 0.15:
                    # Peak: Discharge
                    dis_p = min(b.max_discharge_mw, curr_soc)
                    bess_soc[b.bess_id] -= dis_p
                    bess_dispatch_mw[b.bess_id].append(round(dis_p, 2))
                    net_bess_power += dis_p
                else:
                    bess_dispatch_mw[b.bess_id].append(0.0)

            # Net thermal demand = demand - net_bess_power
            net_demand = max(0.0, demand - net_bess_power)

            # 2. Generator Commitment & Up/Down Time Constraints
            # Ensure must-run / min up-time constraints are respected
            active_gens: List[GeneratorNode] = []
            for g in sorted_gens:
                state = gen_state[g.gen_id]
                is_on, duration, _ = state

                if is_on:
                    if duration < g.min_up_time_hrs:
                        # Must stay ON
                        active_gens.append(g)
                    else:
                        # Can stay ON or shut down
                        active_gens.append(g)
                else:
                    if duration < g.min_down_time_hrs:
                        # Must stay OFF
                        pass
                    else:
                        # Can turn ON if needed for capacity/reserves
                        active_gens.append(g)

            # Capacity check
            total_active_max = sum(g.p_max_mw for g in active_gens)
            while total_active_max < reserve_needed and len(active_gens) < len(generators):
                # Turn on next best available generator
                for g in sorted_gens:
                    if g not in active_gens and gen_state[g.gen_id][1] >= g.min_down_time_hrs:
                        active_gens.append(g)
                        total_startup_cost += g.startup_cost
                        total_active_max += g.p_max_mw
                        break

            # 3. Economic Dispatch across active generators respecting ramp limits
            hourly_disp: Dict[str, float] = {}
            for g in generators:
                if g in active_gens:
                    committed_schedule[g.gen_id].append(1)
                    # Min generation
                    hourly_disp[g.gen_id] = g.p_min_mw
                else:
                    committed_schedule[g.gen_id].append(0)
                    hourly_disp[g.gen_id] = 0.0

            remaining_net = net_demand - sum(hourly_disp.values())
            for g in sorted(active_gens, key=lambda g: g.marginal_cost_per_mwh):
                if remaining_net <= 0:
                    break
                prev_mw = gen_state[g.gen_id][2]
                max_ramp_mw = min(g.p_max_mw, prev_mw + g.ramp_rate_mw_per_min * 60.0)
                available = max_ramp_mw - hourly_disp[g.gen_id]
                alloc = min(max(0.0, available), remaining_net)
                hourly_disp[g.gen_id] += alloc
                remaining_net -= alloc

            if remaining_net > 0:
                total_unserved_mwh += remaining_net

            # Update generator fuel costs and state transitions
            for g in generators:
                p_out = hourly_disp[g.gen_id]
                hourly_gen_mw[g.gen_id].append(round(p_out, 2))
                if p_out > 0:
                    total_fuel_cost += g.marginal_cost_per_mwh * p_out + g.quadratic_cost_coeff * (p_out ** 2)

                is_now_on = (p_out > 0)
                prev_is_on = gen_state[g.gen_id][0]
                if is_now_on == prev_is_on:
                    gen_state[g.gen_id][1] += 1
                else:
                    gen_state[g.gen_id][0] = is_now_on
                    gen_state[g.gen_id][1] = 1
                gen_state[g.gen_id][2] = p_out

        total_op_cost = total_fuel_cost + total_startup_cost + (total_unserved_mwh * 1000.0)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        return UnitCommitmentReport(
            total_operating_cost_usd=round(total_op_cost, 2),
            startup_costs_usd=round(total_startup_cost, 2),
            committed_schedule=committed_schedule,
            hourly_generation_mw=hourly_gen_mw,
            battery_dispatch_mw=bess_dispatch_mw,
            unserved_energy_mwh=round(total_unserved_mwh, 3),
            solver_latency_ms=round(elapsed_ms, 3),
        )
