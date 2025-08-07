#!/usr/bin/env python3
"""
Unit tests for analysis modules
"""

import unittest
import numpy as np
import pandas as pd

from analysis.statistical import StatisticalAnalyzer
from analysis.vacuum import VacuumAnalyzer
from analysis.data_quality import DataQualityAnalyzer, QualityReport


class TestStatisticalAnalyzer(unittest.TestCase):
    """Test statistical analysis"""

    def setUp(self):
        """Set up test data"""
        np.random.seed(42)
        self.data = np.random.randn(100)
        self.analyzer = StatisticalAnalyzer()

    def test_basic_stats(self):
        """Test basic statistics calculation"""
        stats = self.analyzer.calculate_basic_stats(self.data)

        self.assertIn('mean', stats)
        self.assertIn('median', stats)
        self.assertIn('std', stats)
        self.assertIn('min', stats)
        self.assertIn('max', stats)
        self.assertEqual(stats['count'], 100)

    def test_normality_test(self):
        """Test normality testing"""
        # Normal data
        normal_data = np.random.randn(100)
        result = self.analyzer.test_normality(normal_data)

        self.assertIn('is_normal', result)
        self.assertIn('shapiro_p', result)

        # Non-normal data
        uniform_data = np.random.uniform(0, 1, 100)
        result = self.analyzer.test_normality(uniform_data)

        self.assertIsNotNone(result['is_normal'])

    def test_correlation(self):
        """Test correlation calculation"""
        x = np.arange(100)
        y = 2 * x + np.random.randn(100)

        corr = self.analyzer.calculate_correlation(x, y)

        self.assertIn('pearson_r', corr)
        self.assertIn('spearman_r', corr)
        self.assertIn('kendall_tau', corr)

        # Strong positive correlation expected
        self.assertGreater(corr['pearson_r'], 0.9)

    def test_outlier_detection(self):
        """Test outlier detection"""
        # Data with outliers
        data = np.random.randn(100)
        data[50] = 10  # Add outlier

        result = self.analyzer.detect_outliers(data, method='iqr')

        self.assertIn('outlier_indices', result)
        self.assertIn('count', result)
        self.assertIn(50, result['outlier_indices'])


class TestVacuumAnalyzer(unittest.TestCase):
    """Test vacuum analysis"""

    def setUp(self):
        """Set up test data"""
        # Simulate vacuum pressure data
        self.pressure_data = np.exp(-np.linspace(0, 5, 100)) + np.random.randn(100) * 0.01
        self.time_data = np.arange(100)
        self.analyzer = VacuumAnalyzer()

    def test_base_pressure(self):
        """Test base pressure calculation"""
        result = self.analyzer.calculate_base_pressure(
            self.pressure_data,
            window_minutes=10,
            sample_rate_hz=1
        )

        self.assertIn('base_pressure', result)
        self.assertIn('stability', result)
        self.assertIn('confidence', result)
        self.assertIsNotNone(result['base_pressure'])

    def test_spike_detection(self):
        """Test pressure spike detection"""
        # Add spikes
        data = self.pressure_data.copy()
        data[30] = 5  # Add spike
        data[60] = 4  # Add another spike

        spikes = self.analyzer.detect_pressure_spikes(data)

        self.assertIsInstance(spikes, list)
        if spikes:
            self.assertIn('start_index', spikes[0])
            self.assertIn('max_pressure', spikes[0])
            self.assertIn('severity', spikes[0])

    def test_leak_rate(self):
        """Test leak rate calculation"""
        result = self.analyzer.calculate_leak_rate(
            self.pressure_data,
            self.time_data,
            volume_liters=1.0
        )

        self.assertIn('leak_rate', result)
        self.assertIn('r_squared', result)
        self.assertIn('confidence', result)


class TestDataQualityAnalyzer(unittest.TestCase):
    """Test data quality analysis"""

    def setUp(self):
        """Set up test data"""
        self.analyzer = DataQualityAnalyzer()
        self.good_data = np.random.randn(100)
        self.bad_data = np.array([0, 0, 0, np.nan, np.nan, 1, 2, 100, 0, 0])

    def test_quality_report(self):
        """Test quality report generation"""
        report = self.analyzer.analyze(self.good_data)

        self.assertIsInstance(report, QualityReport)
        self.assertEqual(report.total_points, 100)
        self.assertGreaterEqual(report.completeness, 0)
        self.assertLessEqual(report.completeness, 1)

    def test_quality_score(self):
        """Test quality scoring"""
        # Good data should have high score
        good_report = self.analyzer.analyze(self.good_data)
        self.assertGreater(good_report.quality_score, 70)

        # Bad data should have low score
        bad_report = self.analyzer.analyze(self.bad_data)
        self.assertLess(bad_report.quality_score, 70)

    def test_issue_detection(self):
        """Test issue detection"""
        report = self.analyzer.analyze(self.bad_data)

        # Should detect zeros
        self.assertGreater(len(report.zeros), 0)

        # Should detect outliers
        self.assertIn(7, report.outliers)  # 100 is an outlier

        # Should have recommendations
        self.assertGreater(len(report.recommendations), 0)


if __name__ == '__main__':
    unittest.main()