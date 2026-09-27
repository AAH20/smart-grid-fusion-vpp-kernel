"""
Tests for IEEE 738 Dynamic Line Rating (DLR) Scheduler.
"""

import unittest
from smart_grid_fusion_vpp_kernel.core.models import ConductorWeatherObservation
from smart_grid_fusion_vpp_kernel.core.dynamic_line_rating_scheduler import DynamicLineRatingScheduler


class TestDynamicLineRatingScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = DynamicLineRatingScheduler()

    def test_cool_windy_weather_boosts_ampacity(self):
        # Cool, windy conditions should yield substantial capacity headroom over 40C static baseline
        cool_weather = ConductorWeatherObservation(
            ambient_temp_c=15.0,
            wind_speed_m_per_s=5.0,
            wind_angle_deg=90.0,
            solar_radiation_w_m2=500.0,
        )
        report = self.scheduler.calculate_rating(cool_weather)
        self.assertGreater(report.dynamic_line_rating_mw, report.static_line_rating_mw)
        self.assertGreater(report.headroom_gain_pct, 15.0)
        self.assertGreater(report.convective_cooling_w_m, 0.0)
        self.assertLessEqual(report.conductor_core_temp_c, 100.0)


if __name__ == "__main__":
    unittest.main()
