#!/usr/bin/env python3
"""
Legacy-compatible data analysis tools
Provides full functionality matching the original application
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks, savgol_filter
from scipy.interpolate import make_interp_spline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DataAnalysisTools:
    """
    Collection of general data analysis methods
    Provides statistical and signal processing functions for data series
    """

    @staticmethod
    def calculate_statistics(data):
        """
        Calculate comprehensive statistics for a data series

        Args:
            data: Array-like data to analyze

        Returns:
            dict: Dictionary containing statistical measures
        """
        data = np.array(data)
        valid_data = data[~np.isnan(data)]
        
        if len(valid_data) == 0:
            return {
                'count': 0,
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
                'skewness': np.nan,
                'kurtosis': np.nan,
                'cv': np.nan
            }

        # Initialize statistics dictionary
        stats_dict = {
            'count': len(valid_data),
            'mean': np.mean(valid_data),
            'median': np.median(valid_data),
            'std': np.std(valid_data),
            'var': np.var(valid_data),
            'min': np.min(valid_data),
            'max': np.max(valid_data),
            'range': np.max(valid_data) - np.min(valid_data),
            'q1': np.percentile(valid_data, 25),
            'q3': np.percentile(valid_data, 75),
            'iqr': np.percentile(valid_data, 75) - np.percentile(valid_data, 25),
            'skewness': stats.skew(valid_data),
            'kurtosis': stats.kurtosis(valid_data),
            'cv': np.std(valid_data) / np.mean(valid_data) if np.mean(valid_data) != 0 else np.nan
        }
        return stats_dict

    @staticmethod
    def find_peaks_and_valleys(x_data, y_data, prominence=None):
        """
        Find peaks (maxima) and valleys (minima) in the data

        Args:
            x_data: X-axis values
            y_data: Y-axis values
            prominence: Minimum prominence of peaks

        Returns:
            dict: Dictionary with peak and valley information
        """
        x_data = np.array(x_data)
        y_data = np.array(y_data)
        
        # Find peaks (local maxima)
        peaks, peak_props = find_peaks(y_data, prominence=prominence)

        # Find valleys by inverting data and finding peaks
        valleys, valley_props = find_peaks(-y_data, prominence=prominence)

        return {
            'peaks': {
                'indices': peaks,
                'x_values': x_data[peaks] if len(peaks) > 0 else np.array([]),
                'y_values': y_data[peaks] if len(peaks) > 0 else np.array([])
            },
            'valleys': {
                'indices': valleys,
                'x_values': x_data[valleys] if len(valleys) > 0 else np.array([]),
                'y_values': y_data[valleys] if len(valleys) > 0 else np.array([])
            }
        }

    @staticmethod
    def calculate_moving_average(data, window_size):
        """
        Calculate moving average of data

        Args:
            data: Input data array
            window_size: Number of points in moving window

        Returns:
            pd.Series: Moving average values
        """
        return pd.Series(data).rolling(window=window_size, center=True).mean()

    @staticmethod
    def calculate_derivative(x_data, y_data):
        """
        Calculate numerical derivative (rate of change)

        Args:
            x_data: X-axis values
            y_data: Y-axis values

        Returns:
            np.array: Derivative values
        """
        return np.gradient(y_data, x_data)

    @staticmethod
    def perform_fft(data, sample_rate=1.0):
        """
        Perform Fast Fourier Transform for frequency analysis

        Args:
            data: Time series data
            sample_rate: Sampling rate in Hz

        Returns:
            tuple: (frequencies, amplitudes) for positive frequencies only
        """
        fft_values = np.fft.fft(data)
        frequencies = np.fft.fftfreq(len(data), 1 / sample_rate)

        positive_freq_idx = frequencies > 0
        return frequencies[positive_freq_idx], np.abs(fft_values[positive_freq_idx])

    @staticmethod
    def calculate_correlation_matrix(dataframe, columns):
        """
        Calculate correlation matrix for selected columns

        Args:
            dataframe: Pandas DataFrame
            columns: List of column names to correlate

        Returns:
            pd.DataFrame: Correlation matrix
        """
        return dataframe[columns].corr()

    @staticmethod
    def perform_regression(x_data, y_data, degree=1):
        """
        Perform polynomial regression on data

        Args:
            x_data: Independent variable values
            y_data: Dependent variable values
            degree: Polynomial degree (1 for linear)

        Returns:
            dict: Regression results including coefficients and predictions
        """
        x_data = np.array(x_data).reshape(-1, 1)
        y_data = np.array(y_data)

        if degree == 1:
            model = LinearRegression()
            model.fit(x_data, y_data)
            y_pred = model.predict(x_data)
            r2 = model.score(x_data, y_data)
            coefficients = [model.intercept_, model.coef_[0]]
        else:
            coefficients = np.polyfit(x_data.flatten(), y_data, degree)
            poly = np.poly1d(coefficients)
            y_pred = poly(x_data.flatten())

            ss_res = np.sum((y_data - y_pred) ** 2)
            ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
            r2 = 1 - (ss_res / ss_tot)

        return {
            'coefficients': coefficients,
            'y_predicted': y_pred,
            'r_squared': r2,
            'residuals': y_data - y_pred
        }

    @staticmethod
    def detect_outliers(data, method='iqr', threshold=1.5):
        """
        Detect outliers in data using various methods

        Args:
            data: Input data array
            method: Detection method ('iqr', 'zscore', 'isolation')
            threshold: Threshold for outlier detection

        Returns:
            np.array: Boolean mask where True indicates outlier
        """
        data = np.array(data)

        if method == 'iqr':
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outliers = (data < lower_bound) | (data > upper_bound)

        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data))
            outliers = z_scores > threshold

        elif method == 'isolation':
            clf = IsolationForest(contamination=0.1, random_state=42)
            outliers = clf.fit_predict(data.reshape(-1, 1)) == -1

        else:
            outliers = np.zeros(len(data), dtype=bool)

        return outliers


class VacuumAnalysisTools:
    """
    Specialized tools for vacuum pressure data analysis
    Provides methods specific to vacuum system characterization
    """

    @staticmethod
    def calculate_base_pressure(pressure_data, window_minutes=10, sample_rate_hz=1):
        """
        Calculate base pressure using a moving window approach

        Args:
            pressure_data: Array of pressure values
            window_minutes: Size of analysis window in minutes
            sample_rate_hz: Data sampling rate in Hz

        Returns:
            tuple: (base_pressure, rolling_min, rolling_std)
        """
        window_size = int(window_minutes * 60 * sample_rate_hz)
        
        rolling_min = pd.Series(pressure_data).rolling(window=window_size, center=True).min()
        rolling_std = pd.Series(pressure_data).rolling(window=window_size, center=True).std()

        if not rolling_std.isna().all():
            most_stable_idx = rolling_std.idxmin()
            base_pressure = rolling_min.iloc[most_stable_idx]
        else:
            base_pressure = np.min(pressure_data)

        return base_pressure, rolling_min, rolling_std

    @staticmethod
    def calculate_noise_metrics(pressure_data, sample_rate_hz=1):
        """
        Calculate noise characteristics in vacuum pressure data

        Args:
            pressure_data: Array of pressure values
            sample_rate_hz: Data sampling rate in Hz

        Returns:
            dict: Dictionary containing noise metrics
        """
        x = np.arange(len(pressure_data))
        coeffs = np.polyfit(x, pressure_data, 2)
        trend = np.polyval(coeffs, x)
        detrended = pressure_data - trend

        noise_rms = np.sqrt(np.mean(detrended ** 2))
        noise_peak_to_peak = np.max(detrended) - np.min(detrended)

        fft_values = np.fft.fft(detrended)
        frequencies = np.fft.fftfreq(len(detrended), 1 / sample_rate_hz)
        power_spectrum = np.abs(fft_values) ** 2

        positive_freq_mask = frequencies > 0
        if np.any(positive_freq_mask):
            dominant_freq_idx = np.argmax(power_spectrum[positive_freq_mask])
            dominant_frequency = frequencies[positive_freq_mask][dominant_freq_idx]
        else:
            dominant_frequency = 0

        return {
            'noise_rms': noise_rms,
            'noise_p2p': noise_peak_to_peak,
            'dominant_freq': dominant_frequency,
            'power_spectrum': power_spectrum[positive_freq_mask],
            'frequencies': frequencies[positive_freq_mask],
            'detrended_signal': detrended
        }

    @staticmethod
    def detect_pressure_spikes(pressure_data, threshold_factor=3, min_spike_duration=1):
        """
        Detect pressure spikes in vacuum data

        Args:
            pressure_data: Array of pressure values
            threshold_factor: Number of standard deviations above mean for spike
            min_spike_duration: Minimum number of points for valid spike

        Returns:
            list: List of dictionaries describing each spike
        """
        rolling_mean = pd.Series(pressure_data).rolling(window=100, center=True).mean()
        rolling_std = pd.Series(pressure_data).rolling(window=100, center=True).std()

        threshold = rolling_mean + threshold_factor * rolling_std
        spike_mask = pressure_data > threshold

        spikes = []
        spike_start = None

        for i, is_spike in enumerate(spike_mask):
            if is_spike and spike_start is None:
                spike_start = i
            elif not is_spike and spike_start is not None:
                duration = i - spike_start
                if duration >= min_spike_duration:
                    max_pressure = np.max(pressure_data[spike_start:i])
                    severity = 'high' if max_pressure > rolling_mean.iloc[spike_start] * 10 else 'medium'

                    spikes.append({
                        'start': spike_start,
                        'end': i,
                        'duration': duration,
                        'max_pressure': max_pressure,
                        'severity': severity
                    })
                spike_start = None

        return spikes

    @staticmethod
    def calculate_leak_rate(pressure_data, time_data, start_pressure, end_pressure=None):
        """
        Calculate vacuum leak rate from pressure rise

        Args:
            pressure_data: Array of pressure values
            time_data: Array of time values
            start_pressure: Initial pressure
            end_pressure: Final pressure

        Returns:
            dict: Dictionary containing leak rate analysis
        """
        if end_pressure is None:
            end_pressure = pressure_data[-1]

        if pd.api.types.is_datetime64_any_dtype(time_data):
            time_seconds = (time_data - time_data.iloc[0]).dt.total_seconds()
        else:
            time_seconds = time_data

        log_pressure = np.log(pressure_data)
        coeffs = np.polyfit(time_seconds, log_pressure, 1)

        leak_rate = coeffs[0] * np.mean(pressure_data)
        fitted = np.exp(np.polyval(coeffs, time_seconds))

        ss_res = np.sum((pressure_data - fitted) ** 2)
        ss_tot = np.sum((pressure_data - np.mean(pressure_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        time_constant = -1 / coeffs[0] if coeffs[0] != 0 else np.inf

        return {
            'leak_rate': leak_rate,
            'r_squared': r_squared,
            'fitted_curve': fitted,
            'time_constant': time_constant
        }

    @staticmethod
    def analyze_pump_down_curve(pressure_data, time_data):
        """
        Analyze pump-down characteristics

        Args:
            pressure_data: Array of pressure values during pump-down
            time_data: Array of corresponding time values

        Returns:
            dict: Dictionary containing pump-down analysis
        """
        initial_pressure = pressure_data[0]
        final_pressure = pressure_data[-1]

        milestones = {}
        pressure_targets = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]

        for target in pressure_targets:
            if final_pressure <= target < initial_pressure:
                idx = np.where(pressure_data <= target)[0]
                if len(idx) > 0:
                    milestones[f"{target:.0e} mbar"] = time_data[idx[0]]

        log_pressure = np.log10(pressure_data)
        d_log_p_dt = np.gradient(log_pressure)

        return {
            'initial_pressure': initial_pressure,
            'final_pressure': final_pressure,
            'milestones': milestones,
            'pumping_speed_indicator': -d_log_p_dt
        }

    @staticmethod
    def calculate_outgassing_rate(pressure_data, time_data, volume_liters):
        """
        Calculate outgassing rate from pressure rise data

        Args:
            pressure_data: Array of pressure values
            time_data: Array of time values
            volume_liters: System volume in liters

        Returns:
            dict: Outgassing analysis results
        """
        if pd.api.types.is_datetime64_any_dtype(time_data):
            time_seconds = (time_data - time_data.iloc[0]).dt.total_seconds()
        else:
            time_seconds = np.array(time_data)

        dp_dt = np.gradient(pressure_data, time_seconds)
        outgassing_rate = volume_liters * dp_dt
        avg_outgassing = np.mean(outgassing_rate)

        return {
            'outgassing_rate': outgassing_rate,
            'average_rate': avg_outgassing,
            'units': 'mbar·L/s'
        }
