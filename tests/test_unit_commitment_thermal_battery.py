"""
Tests for 24-Hour Thermal & Battery Unit Commitment Solver.
"""

import unittest
from smart_grid_fusion_vpp_kernel.core.models import GeneratorNode, BatteryStorageUnit
from smart_grid_fusion_vpp_kernel.core.unit_commitment_thermal_battery import UnitCommitmentThermalBatterySolver


class TestUnitCommitmentThermalBattery(unittest.TestCase):
    def setUp(self):
        self.solver = UnitCommitmentThermalBatterySolver()
        self.gens = [
            GeneratorNode("g_base", "b1", 50.0, 300.0, 20.0, min_up_time_hrs=4, startup_cost=1000.0),
            GeneratorNode("g_peak", "b2", 10.0, 150.0, 45.0, min_up_time_hrs=1, startup_cost=200.0),
        ]
        self.batteries = [
            BatteryStorageUnit("bess_1", "b1", capacity_mwh=100.0, max_charge_mw=25.0, max_discharge_mw=25.0),
        ]
        # 6-hour test profile
        self.demands = [100.0, 80.0, 120.0, 250.0, 320.0, 200.0]

    def test_commitment_and_bess_discharge(self):
        report = self.solver.solve_commitment(self.gens, self.batteries, self.demands)
        self.assertEqual(len(report.hourly_generation_mw["g_base"]), 6)
        self.assertEqual(len(report.battery_dispatch_mw["bess_1"]), 6)
        self.assertGreater(report.total_operating_cost_usd, 0.0)
        # Verify base generator committed
        self.assertIn(1, report.committed_schedule["g_base"])


if __name__ == "__main__":
    unittest.main()
