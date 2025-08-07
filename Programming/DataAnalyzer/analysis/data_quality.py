#!/usr/bin/env python3
"""
Data quality analysis and validation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Data quality analysis report"""

    total_points: int
    valid_points: int
    missing_points: int

    # Issues
    zeros: List[int] = None
    outliers: List[int] = None
    duplicates: List[int] = None
    gaps: List[Tuple[int, int]] = None

    # Metrics
    completeness: float = 0.0
    consistency: float = 0.0
    validity: float = 0.0

    # Recommendations
    recommendations: List[str] = None

    def __post_init__(self):
        if self.zeros is None:
            self.zeros = []
        if self.outliers is None:
            self.outliers = []
        if self.duplicates is None:
            self.duplicates = []
        if self.gaps is None:
            self.gaps = []
        if self.recommendations is None:
            self.recommendations = []

    @property
    def quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        return (self.completeness + self.consistency + self.validity) / 3 * 100

    @property
    def quality_grade(self) -> str:
        """Get quality grade"""
        score = self.quality_score
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


class DataQualityAnalyzer:
    """Analyzes data quality and identifies issues"""

    def __init__(self):
        self.config = {
            'zero_threshold': 1e-10,
            'outlier_method': 'iqr',
            'outlier_threshold': 3.0,
            'duplicate_threshold': 1e-6,
            'gap_threshold': 10,
            'noise_window': 50
        }

    def analyze(self, data: np.ndarray, timestamps: Optional[np.ndarray] = None) -> QualityReport:
        """
        Perform comprehensive data quality analysis

        Args:
            data: Data values to analyze
            timestamps: Optional timestamp array

        Returns:
            QualityReport with analysis results
        """
        report = QualityReport(
            total_points=len(data),
            valid_points=np.sum(~np.isnan(data)),
            missing_points=np.sum(np.isnan(data))
        )

        # Analyze different aspects
        self._check_zeros(data, report)
        self._check_outliers(data, report)
        self._check_duplicates(data, report)

        if timestamps is not None:
            self._check_gaps(timestamps, report)

        # Calculate metrics
        self._calculate_metrics(data, report)

        # Generate recommendations
        self._generate_recommendations(report)

        return report

    def _check_zeros(self, data: np.ndarray, report: QualityReport):
        """Check for zero or near-zero values"""
        threshold = self.config['zero_threshold']
        zeros = np.where(np.abs(data) < threshold)[0]
        report.zeros = zeros.tolist()

    def _check_outliers(self, data: np.ndarray, report: QualityReport):
        """Check for outliers"""
        clean_data = data[~np.isnan(data)]

        if len(clean_data) < 3:
            return

        method = self.config['outlier_method']
        threshold = self.config['outlier_threshold']

        if method == 'iqr':
            q1 = np.percentile(clean_data, 25)
            q3 = np.percentile(clean_data, 75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outliers = np.where((data < lower) | (data > upper))[0]

        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(clean_data))
            outliers = np.where(z_scores > threshold)[0]

        else:
            outliers = np.array([])

        report.outliers = outliers.tolist()

    def _check_duplicates(self, data: np.ndarray, report: QualityReport):
        """Check for duplicate consecutive values"""
        threshold = self.config['duplicate_threshold']
        duplicates = []

        for i in range(1, len(data)):
            if not np.isnan(data[i]) and not np.isnan(data[i - 1]):
                if np.abs(data[i] - data[i - 1]) < threshold:
                    duplicates.append(i)

        # Group consecutive duplicates
        if duplicates:
            grouped = []
            start = duplicates[0]

            for i in range(1, len(duplicates)):
                if duplicates[i] != duplicates[i - 1] + 1:
                    grouped.append(start)
                    start = duplicates[i]
            grouped.append(start)

            report.duplicates = grouped

    def _check_gaps(self, timestamps: np.ndarray, report: QualityReport):
        """Check for gaps in time series"""
        if len(timestamps) < 2:
            return

        # Calculate time differences
        diffs = np.diff(timestamps)
        median_diff = np.median(diffs)

        # Find gaps (differences significantly larger than median)
        threshold = self.config['gap_threshold']
        gap_indices = np.where(diffs > threshold * median_diff)[0]

        gaps = []
        for idx in gap_indices:
            gaps.append((idx, idx + 1))

        report.gaps = gaps

    def _calculate_metrics(self, data: np.ndarray, report: QualityReport):
        """Calculate quality metrics"""

        # Completeness: ratio of non-missing values
        report.completeness = report.valid_points / report.total_points if report.total_points > 0 else 0

        # Consistency: inverse of coefficient of variation
        clean_data = data[~np.isnan(data)]
        if len(clean_data) > 0:
            cv = np.std(clean_data) / np.mean(clean_data) if np.mean(clean_data) != 0 else 1
            report.consistency = 1 / (1 + cv)
        else:
            report.consistency = 0

        # Validity: ratio of non-problematic points
        problem_count = len(report.zeros) + len(report.outliers) + len(report.duplicates)
        report.validity = 1 - (problem_count / report.total_points) if report.total_points > 0 else 0

    def _generate_recommendations(self, report: QualityReport):
        """Generate recommendations based on issues found"""

        if report.missing_points > report.total_points * 0.1:
            report.recommendations.append(
                f"High amount of missing data ({report.missing_points}/{report.total_points}). "
                "Consider interpolation or filtering."
            )

        if len(report.zeros) > report.total_points * 0.05:
            report.recommendations.append(
                f"Many zero values detected ({len(report.zeros)}). "
                "Check sensor calibration or data collection."
            )

        if len(report.outliers) > report.total_points * 0.02:
            report.recommendations.append(
                f"Multiple outliers found ({len(report.outliers)}). "
                "Consider outlier removal or investigation."
            )

        if len(report.duplicates) > report.total_points * 0.1:
            report.recommendations.append(
                f"Many duplicate values ({len(report.duplicates)}). "
                "Check if sensor is stuck or data is repeated."
            )

        if report.gaps:
            report.recommendations.append(
                f"Time series gaps detected ({len(report.gaps)}). "
                "Consider interpolation for continuity."
            )

        if report.quality_score < 70:
            report.recommendations.append(
                "Overall data quality is poor. Manual review recommended."
            )


class DataCleaner:
    """Data cleaning utilities"""

    @staticmethod
    def remove_outliers(data: np.ndarray, method: str = 'iqr', threshold: float = 3.0) -> np.ndarray:
        """Remove outliers from data"""
        clean_data = data.copy()

        if method == 'iqr':
            q1 = np.percentile(data[~np.isnan(data)], 25)
            q3 = np.percentile(data[~np.isnan(data)], 75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            clean_data[(clean_data < lower) | (clean_data > upper)] = np.nan

        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data[~np.isnan(data)]))
            clean_data[z_scores > threshold] = np.nan

        return clean_data

    @staticmethod
    def fill_gaps(data: np.ndarray, method: str = 'linear') -> np.ndarray:
        """Fill gaps in data"""
        series = pd.Series(data)

        if method == 'linear':
            filled = series.interpolate(method='linear')
        elif method == 'polynomial':
            filled = series.interpolate(method='polynomial', order=2)
        elif method == 'forward':
            filled = series.fillna(method='ffill')
        elif method == 'backward':
            filled = series.fillna(method='bfill')
        elif method == 'mean':
            filled = series.fillna(series.mean())
        else:
            filled = series

        return filled.values

    @staticmethod
    def smooth_data(data: np.ndarray, window: int = 5, method: str = 'moving_average') -> np.ndarray:
        """Smooth noisy data"""
        from scipy.signal import savgol_filter

        if method == 'moving_average':
            series = pd.Series(data)
            smoothed = series.rolling(window=window, center=True).mean()
            return smoothed.fillna(data).values

        elif method == 'savgol':
            if len(data) > window:
                return savgol_filter(data, window, min(3, window - 1))
            return data

        elif method == 'exponential':
            series = pd.Series(data)
            smoothed = series.ewm(span=window, adjust=False).mean()
            return smoothed.values

        return data