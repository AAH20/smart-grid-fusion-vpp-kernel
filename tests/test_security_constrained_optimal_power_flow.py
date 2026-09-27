"""
Tests for Security-Constrained Optimal Power Flow (SC-OPF).
"""

import unittest
from smart_grid_fusion_vpp_kernel.core.models import GeneratorNode, TransmissionBranch
from smart_grid_fusion_vpp_kernel.core.security_constrained_optimal_power_flow import SecurityConstrainedOptimalPowerFlow


class TestSecurityConstrainedOPF(unittest.TestCase):
    def setUp(self):
        self.solver = SecurityConstrainedOptimalPowerFlow()
        self.buses = ["b1", "b2", "b3"]
        self.branches = [
            TransmissionBranch("l1_2", "b1", "b2", 0.05, 100.0, True),
            TransmissionBranch("l2_3", "b2", "b3", 0.05, 100.0, True),
            TransmissionBranch("l1_3", "b1", "b3", 0.10, 80.0, True),
        ]
        self.gens = [
            GeneratorNode("g1", "b1", 10.0, 200.0, 20.0),
            GeneratorNode("g2", "b2", 10.0, 150.0, 35.0),
        ]
        self.demands = {"b1": 0.0, "b2": 100.0, "b3": 80.0}

    def test_sc_opf_solution_and_balance(self):
        res = self.solver.solve_sc_opf(self.buses, self.branches, self.gens, self.demands)
        total_gen = sum(res.base_dispatch_mw.values())
        total_load = sum(self.demands.values())
        self.assertAlmostEqual(total_gen, total_load, places=1)
        self.assertGreater(res.total_cost_usd, 0.0)
        self.assertIn("b1", res.marginal_locational_prices)
        self.assertGreater(len(res.branch_flows_mw), 0)


if __name__ == "__main__":
    unittest.main()
