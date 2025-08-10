#!/usr/bin/env python3
"""
Statistical analysis tools - FIXED VERSION
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """Fixed Statistical analysis methods (no self in static methods)"""

    @staticmethod
    def calculate_basic_stats(data: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistical measures"""
        clean_data = data[~np.isnan(data)]

        if len(clean_data) == 0:
            return {
                'count': 0,
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'q1': np.nan,
                'q3': np.nan,
                'iqr': np.nan,
                'skewness': np.nan,
                'kurtosis': np.nan
            }

        return {
            'count': len(clean_data),
            'mean': float(np.mean(clean_data)),
            'median': float(np.median(clean_data)),
            'std': float(np.std(clean_data)),
            'min': float(np.min(clean_data)),
            'max': float(np.max(clean_data)),
            'q1': float(np.percentile(clean_data, 25)),
            'q3': float(np.percentile(clean_data, 75)),
            'iqr': float(np.percentile(clean_data, 75) - np.percentile(clean_data, 25)),
            'skewness': float(stats.skew(clean_data)),
            'kurtosis': float(stats.kurtosis(clean_data))
        }

    @staticmethod
    def test_normality(data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
        """Test for normality"""
        clean_data = data[~np.isnan(data)]

        if len(clean_data) < 3:
            return {
                'is_normal': False,
                'shapiro_stat': np.nan,
                'shapiro_p': np.nan,
                'anderson_stat': np.nan,
                'anderson_critical': [],
                'statistic': np.nan,
                'p_value': np.nan
            }

        shapiro_stat, shapiro_p = stats.shapiro(clean_data)
        anderson_result = stats.anderson(clean_data)
        is_normal = shapiro_p > alpha

        return {
            'is_normal': bool(is_normal),
            'shapiro_stat': float(shapiro_stat),
            'shapiro_p': float(shapiro_p),
            'anderson_stat': float(anderson_result.statistic),
            'anderson_critical': anderson_result.critical_values.tolist(),
            'statistic': float(shapiro_stat),
            'p_value': float(shapiro_p)
        }

    @staticmethod
    def calculate_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """Calculate correlation coefficient"""
        mask = ~(np.isnan(x) | np.isnan(y))
        clean_x = x[mask]
        clean_y = y[mask]

        if len(clean_x) < 2:
            return 0.0

        corr_matrix = np.corrcoef(clean_x, clean_y)
        return float(corr_matrix[0, 1])

    @staticmethod
    def detect_outliers(data: np.ndarray, method: str = 'iqr',
                       threshold: float = 1.5) -> List[int]:
        """Detect outliers - returns list of indices"""
        clean_data = data[~np.isnan(data)]

        if len(clean_data) < 3:
            return []

        outlier_indices = []

        if method == 'iqr':
            q1 = np.percentile(clean_data, 25)
            q3 = np.percentile(clean_data, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for i, val in enumerate(data):
                if not np.isnan(val) and (val < lower_bound or val > upper_bound):
                    outlier_indices.append(i)

        elif method == 'zscore':
            z_threshold = threshold if threshold > 1 else 3.0
            data_z_scores = np.full(len(data), np.nan)
            data_z_scores[~np.isnan(data)] = np.abs(stats.zscore(data[~np.isnan(data)]))

            for i, z in enumerate(data_z_scores):
                if not np.isnan(z) and z > z_threshold:
                    outlier_indices.append(i)

        return outlier_indices
