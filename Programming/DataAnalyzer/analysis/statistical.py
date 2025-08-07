#!/usr/bin/env python3
"""
Statistical analysis tools
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks, savgol_filter
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """Statistical analysis methods"""

    @staticmethod
    def calculate_basic_stats(data: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
        """Calculate basic statistics"""
        data_clean = np.array(data)[~np.isnan(data)]

        if len(data_clean) == 0:
            return {
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'var': np.nan,
                'min': np.nan,
                'max': np.nan,
                'range': np.nan,
                'q1': np.nan,
                'q3': np.nan,
                'iqr': np.nan,
                'cv': np.nan,
                'skewness': np.nan,
                'kurtosis': np.nan,
                'count': 0
            }

        return {
            'mean': float(np.mean(data_clean)),
            'median': float(np.median(data_clean)),
            'std': float(np.std(data_clean)),
            'var': float(np.var(data_clean)),
            'min': float(np.min(data_clean)),
            'max': float(np.max(data_clean)),
            'range': float(np.max(data_clean) - np.min(data_clean)),
            'q1': float(np.percentile(data_clean, 25)),
            'q3': float(np.percentile(data_clean, 75)),
            'iqr': float(np.percentile(data_clean, 75) - np.percentile(data_clean, 25)),
            'cv': float(np.std(data_clean) / np.mean(data_clean)) if np.mean(data_clean) != 0 else np.nan,
            'skewness': float(stats.skew(data_clean)),
            'kurtosis': float(stats.kurtosis(data_clean)),
            'count': len(data_clean)
        }

    @staticmethod
    def test_normality(data: np.ndarray) -> Dict[str, Any]:
        """Test data for normality"""
        data_clean = data[~np.isnan(data)]

        if len(data_clean) < 3:
            return {
                'is_normal': None,
                'shapiro_stat': np.nan,
                'shapiro_p': np.nan,
                'anderson_stat': np.nan,
                'anderson_critical': []
            }

        # Shapiro-Wilk test
        shapiro_stat, shapiro_p = stats.shapiro(data_clean)

        # Anderson-Darling test
        anderson_result = stats.anderson(data_clean)

        return {
            'is_normal': shapiro_p > 0.05,
            'shapiro_stat': float(shapiro_stat),
            'shapiro_p': float(shapiro_p),
            'anderson_stat': float(anderson_result.statistic),
            'anderson_critical': anderson_result.critical_values.tolist()
        }

    @staticmethod
    def calculate_correlation(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Calculate correlation between two arrays"""
        # Remove NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]

        if len(x_clean) < 2:
            return {
                'pearson_r': np.nan,
                'pearson_p': np.nan,
                'spearman_r': np.nan,
                'spearman_p': np.nan,
                'kendall_tau': np.nan,
                'kendall_p': np.nan
            }

        # Pearson correlation
        pearson_r, pearson_p = stats.pearsonr(x_clean, y_clean)

        # Spearman correlation
        spearman_r, spearman_p = stats.spearmanr(x_clean, y_clean)

        # Kendall's tau
        kendall_tau, kendall_p = stats.kendalltau(x_clean, y_clean)

        return {
            'pearson_r': float(pearson_r),
            'pearson_p': float(pearson_p),
            'spearman_r': float(spearman_r),
            'spearman_p': float(spearman_p),
            'kendall_tau': float(kendall_tau),
            'kendall_p': float(kendall_p)
        }

    @staticmethod
    def perform_regression(x: np.ndarray, y: np.ndarray, degree: int = 1) -> Dict[str, Any]:
        """Perform polynomial regression"""
        # Remove NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask].reshape(-1, 1)
        y_clean = y[mask]

        if len(x_clean) < degree + 1:
            return {
                'coefficients': [],
                'r_squared': np.nan,
                'predictions': [],
                'residuals': []
            }

        if degree == 1:
            # Linear regression
            model = LinearRegression()
            model.fit(x_clean, y_clean)
            predictions = model.predict(x_clean)
            coefficients = [model.intercept_, model.coef_[0]]
        else:
            # Polynomial regression
            poly = PolynomialFeatures(degree=degree)
            x_poly = poly.fit_transform(x_clean)
            model = LinearRegression()
            model.fit(x_poly, y_clean)
            predictions = model.predict(x_poly)
            coefficients = [model.intercept_] + model.coef_[1:].tolist()

        # Calculate R-squared
        ss_res = np.sum((y_clean - predictions) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return {
            'coefficients': coefficients,
            'r_squared': float(r_squared),
            'predictions': predictions.tolist(),
            'residuals': (y_clean - predictions).tolist()
        }

    @staticmethod
    def detect_outliers(data: np.ndarray, method: str = 'iqr', threshold: float = 1.5) -> Dict[str, Any]:
        """Detect outliers in data"""
        data_clean = data[~np.isnan(data)]

        if len(data_clean) < 3:
            return {
                'outlier_indices': [],
                'outlier_values': [],
                'lower_bound': np.nan,
                'upper_bound': np.nan,
                'count': 0
            }

        if method == 'iqr':
            # IQR method
            q1 = np.percentile(data_clean, 25)
            q3 = np.percentile(data_clean, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

        elif method == 'zscore':
            # Z-score method
            mean = np.mean(data_clean)
            std = np.std(data_clean)
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std

        elif method == 'mad':
            # Median Absolute Deviation method
            median = np.median(data_clean)
            mad = np.median(np.abs(data_clean - median))
            lower_bound = median - threshold * mad
            upper_bound = median + threshold * mad

        else:
            raise ValueError(f"Unknown outlier method: {method}")

        # Find outliers
        outlier_mask = (data_clean < lower_bound) | (data_clean > upper_bound)
        outlier_indices = np.where(outlier_mask)[0].tolist()
        outlier_values = data_clean[outlier_mask].tolist()

        return {
            'outlier_indices': outlier_indices,
            'outlier_values': outlier_values,
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'count': len(outlier_indices),
            'percentage': len(outlier_indices) / len(data_clean) * 100
        }

    @staticmethod
    def time_series_decomposition(data: pd.Series, period: int = None) -> Dict[str, np.ndarray]:
        """Decompose time series into trend, seasonal, and residual components"""
        from statsmodels.tsa.seasonal import seasonal_decompose

        if len(data) < 2:
            return {
                'trend': np.array([]),
                'seasonal': np.array([]),
                'residual': np.array([])
            }

        # Auto-detect period if not provided
        if period is None:
            period = min(len(data) // 2, 12)

        try:
            decomposition = seasonal_decompose(data, model='additive', period=period)

            return {
                'trend': decomposition.trend.values,
                'seasonal': decomposition.seasonal.values,
                'residual': decomposition.resid.values
            }
        except Exception as e:
            logger.warning(f"Time series decomposition failed: {e}")
            return {
                'trend': np.array([]),
                'seasonal': np.array([]),
                'residual': np.array([])
            }

    @staticmethod
    def fft_analysis(data: np.ndarray, sample_rate: float = 1.0) -> Dict[str, Any]:
        """Perform FFT frequency analysis"""
        data_clean = data[~np.isnan(data)]

        if len(data_clean) < 2:
            return {
                'frequencies': [],
                'amplitudes': [],
                'dominant_frequency': np.nan,
                'dominant_amplitude': np.nan
            }

        # Compute FFT
        fft_values = np.fft.fft(data_clean)
        frequencies = np.fft.fftfreq(len(data_clean), 1 / sample_rate)

        # Get positive frequencies only
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        amplitudes = np.abs(fft_values[positive_freq_idx])

        # Find dominant frequency
        if len(amplitudes) > 0:
            dominant_idx = np.argmax(amplitudes)
            dominant_frequency = frequencies[dominant_idx]
            dominant_amplitude = amplitudes[dominant_idx]
        else:
            dominant_frequency = np.nan
            dominant_amplitude = np.nan

        return {
            'frequencies': frequencies.tolist(),
            'amplitudes': amplitudes.tolist(),
            'dominant_frequency': float(dominant_frequency),
            'dominant_amplitude': float(dominant_amplitude)
        }