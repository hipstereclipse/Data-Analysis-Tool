#!/usr/bin/env python3
"""
Focused tests for annotation pathways, including datetime handling and spike/base/leak/pumpdown helpers.
"""

import unittest
import datetime as dt

from core.annotation_manager import AnnotationManager
from models.data_models import AnnotationConfig


class TestAnnotationManager(unittest.TestCase):
    def setUp(self):
        self.mgr = AnnotationManager()

    def test_add_spike_annotation_point_fields(self):
        ann = self.mgr.add_spike_annotation(x=10.0, y=1.23e-3, magnitude=1.23e-3, series_name="S1")
        self.assertEqual(ann.annotation_type, "point")
        self.assertEqual(ann.x, 10.0)
        self.assertEqual(ann.y, 1.23e-3)
        self.assertTrue(any(a.annotation_id == ann.annotation_id for a in self.mgr.annotations))

    def test_add_base_pressure_line(self):
        ann = self.mgr.add_base_pressure_annotation(x_start=0.0, x_end=100.0, pressure=1e-6, series_name="S1")
        self.assertEqual(ann.annotation_type, "line")
        self.assertEqual(ann.y, 1e-6)
        self.assertEqual(ann.y2, 1e-6)

    def test_add_leak_line(self):
        ann = self.mgr.add_leak_annotation(x_start=0.0, x_end=10.0, leak_rate=1e-8, series_name="S1")
        self.assertEqual(ann.annotation_type, "line")
        self.assertAlmostEqual(ann.x, 0.0)
        self.assertAlmostEqual(ann.x2, 10.0)

    def test_datetime_normalization_no_crash(self):
        # Ensure draw does not crash when given datetime x values
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        self.mgr.set_data_context(ax)
        t0 = dt.datetime(2024, 1, 1, 0, 0, 0)
        ann = AnnotationConfig(annotation_type="point", x=t0, y=1.0, color="red")
        self.mgr.add_annotation(ann)
        # Should be able to draw all without raising
        self.mgr.draw_all_annotations(ax)
        plt.close(fig)


if __name__ == '__main__':
    unittest.main()
