"""
Tests for Tokamak Plasma MHD Equilibrium & Poloidal Field Coil Solver.
"""

import unittest
from smart_grid_fusion_vpp_kernel.core.models import PoloidalFieldCoil
from smart_grid_fusion_vpp_kernel.core.tokamak_plasma_mhd_equilibrium import TokamakPlasmaMHDEquilibriumSolver


class TestTokamakPlasmaMHDSolver(unittest.TestCase):
    def setUp(self):
        self.solver = TokamakPlasmaMHDEquilibriumSolver()
        self.coils = [
            PoloidalFieldCoil("pf_top", radius_r_m=2.0, height_z_m=2.0, max_current_ka=40.0, turns=100),
            PoloidalFieldCoil("pf_bot", radius_r_m=2.0, height_z_m=-2.0, max_current_ka=40.0, turns=100),
            PoloidalFieldCoil("pf_mid", radius_r_m=4.0, height_z_m=0.0, max_current_ka=40.0, turns=100),
        ]

    def test_tokamak_equilibrium_solution(self):
        report = self.solver.solve_equilibrium(
            self.coils,
            target_major_radius_r0=3.0,
            target_minor_radius_a=1.0,
            target_elongation_kappa=1.7,
            target_triangularity_delta=0.33,
            plasma_current_ma=12.0,
        )
        self.assertEqual(report.plasma_current_ma, 12.0)
        self.assertEqual(report.elongation_kappa, 1.7)
        self.assertEqual(len(report.coil_currents_ka), 3)
        self.assertGreater(report.confinement_quality_factor, 1.0)
        # Verify X-point coordinates are returned
        self.assertIsInstance(report.x_point_coordinates, tuple)
        self.assertEqual(len(report.x_point_coordinates), 2)


if __name__ == "__main__":
    unittest.main()
