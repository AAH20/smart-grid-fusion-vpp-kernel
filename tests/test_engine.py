"""
Tests for Smart Grid, Fusion Tokamak & VPP Engine.
"""

import unittest
from smart_grid_fusion_vpp_kernel.engine import SmartGridFusionVPPEngine


class TestSmartGridFusionVPPEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SmartGridFusionVPPEngine()

    def test_full_pipeline_benchmark(self):
        report = self.engine.run_full_pipeline_benchmark()
        self.assertGreater(report.total_runtime_ms, 0.0)
        self.assertLess(report.total_runtime_ms, 1000.0)  # sub-second execution
        self.assertGreater(report.sc_opf_summary["total_cost_usd"], 0.0)
        self.assertGreater(report.unit_commitment_summary["operating_cost_usd"], 0.0)
        self.assertGreater(report.vpp_co_optimization_summary["net_profit_usd"], 0.0)
        self.assertEqual(report.tokamak_mhd_summary["plasma_current_ma"], 15.0)
        self.assertGreater(report.dlr_scheduling_summary["headroom_gain_mw"], 0.0)


if __name__ == "__main__":
    unittest.main()
