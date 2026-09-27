"""
Tests for Virtual Power Plant (VPP) Dual-Market Co-Optimizer.
"""

import unittest
from smart_grid_fusion_vpp_kernel.core.models import DistributedEnergyResource
from smart_grid_fusion_vpp_kernel.core.virtual_power_plant_co_optimizer import VirtualPowerPlantCoOptimizer


class TestVirtualPowerPlantCoOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = VirtualPowerPlantCoOptimizer()
        self.ders = [
            DistributedEnergyResource("solar_1", "solar", 50.0, 40.0, 0.0, 2.0),
            DistributedEnergyResource("battery_1", "battery", 30.0, 30.0, 5.0, 10.0),
        ]

    def test_co_optimization_profit_and_allocation(self):
        report = self.optimizer.co_optimize(self.ders, wholesale_energy_price_mwh=40.0, regulation_clearing_price_mw=70.0)
        self.assertGreater(report.net_economic_profit_usd, 0.0)
        self.assertGreater(report.frequency_regulation_revenue_usd, 0.0)
        self.assertGreater(report.ancillary_reserve_committed_mw, 0.0)
        self.assertIn("solar_1", report.der_allocations)
        self.assertIn("battery_1", report.der_allocations)


if __name__ == "__main__":
    unittest.main()
