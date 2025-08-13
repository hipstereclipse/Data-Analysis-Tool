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
        try:
            # Ensure we have enough data
            if len(pressure_data) < 10:
                return []
                
            # Handle NaN values
            pressure_clean = pd.Series(pressure_data).dropna()
            if len(pressure_clean) < 10:
                return []
            
            # Dynamic window size based on data length
            window_size = min(100, max(10, len(pressure_clean) // 10))
            
            rolling_mean = pressure_clean.rolling(window=window_size, center=True).mean()
            rolling_std = pressure_clean.rolling(window=window_size, center=True).std()
            
            # Fill NaN values at edges
            rolling_mean = rolling_mean.fillna(method='bfill').fillna(method='ffill')
            rolling_std = rolling_std.fillna(method='bfill').fillna(method='ffill')

            threshold = rolling_mean + threshold_factor * rolling_std
            spike_mask = pressure_clean > threshold

            spikes = []
            spike_start = None

            for i, is_spike in enumerate(spike_mask):
                if is_spike and spike_start is None:
                    spike_start = i
                elif not is_spike and spike_start is not None:
                    duration = i - spike_start
                    if duration >= min_spike_duration:
                        spike_data = pressure_clean.iloc[spike_start:i]
                        max_pressure = spike_data.max()
                        baseline = rolling_mean.iloc[spike_start]
                        
                        # Improved severity classification
                        pressure_ratio = max_pressure / baseline if baseline > 0 else float('inf')
                        if pressure_ratio > 100:
                            severity = 'critical'
                        elif pressure_ratio > 10:
                            severity = 'high'
                        elif pressure_ratio > 3:
                            severity = 'medium'
                        else:
                            severity = 'low'

                        spikes.append({
                            'start': spike_start,
                            'end': i,
                            'duration': duration,
                            'max_pressure': max_pressure,
                            'baseline_pressure': baseline,
                            'pressure_ratio': pressure_ratio,
                            'severity': severity,
                            'spike_magnitude': max_pressure - baseline,
                            'time_indices': list(range(spike_start, i))
                        })
                    spike_start = None

            return spikes
            
        except Exception as e:
            logger.error(f"Error in spike detection: {e}")
            return []

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
        try:
            if end_pressure is None:
                if hasattr(pressure_data, '__getitem__'):
                    end_pressure = pressure_data[-1]
                else:
                    end_pressure = pressure_data

            # Clean data and ensure consistent types
            mask = ~(pd.isna(pressure_data) | pd.isna(time_data))
            pressure_clean = pressure_data[mask]
            time_clean = time_data[mask]
            
            # Convert to pandas Series for consistent handling
            if not isinstance(pressure_clean, pd.Series):
                pressure_clean = pd.Series(pressure_clean, name='pressure')
            if not isinstance(time_clean, pd.Series):
                time_clean = pd.Series(time_clean, name='time')
            
            if len(pressure_clean) < 2:
                return {}

            # Convert time to numeric if needed
            if hasattr(time_clean, 'iloc'):
                # pandas Series
                if pd.api.types.is_datetime64_any_dtype(time_clean):
                    time_seconds = (time_clean - time_clean.iloc[0]).dt.total_seconds()
                else:
                    time_seconds = time_clean - time_clean.iloc[0]
            else:
                # numpy array
                if pd.api.types.is_datetime64_any_dtype(time_clean):
                    time_seconds = (pd.Series(time_clean) - pd.Series(time_clean)[0]).dt.total_seconds()
                else:
                    time_seconds = time_clean - time_clean[0]

            # Multiple leak rate calculation methods
            results = {}
            
            # Method 1: Linear fit to pressure vs time
            try:
                coeffs_linear = np.polyfit(time_seconds, pressure_clean, 1)
                linear_leak_rate = coeffs_linear[0]  # mbar/s
                linear_fit_quality = np.corrcoef(pressure_clean, 
                                               np.polyval(coeffs_linear, time_seconds))[0, 1] ** 2
                results['linear'] = {
                    'leak_rate': linear_leak_rate,
                    'fit_quality': linear_fit_quality,
                    'units': 'mbar/s'
                }
            except:
                results['linear'] = {'leak_rate': 0, 'fit_quality': 0, 'units': 'mbar/s'}

            # Method 2: Exponential fit to log(pressure) vs time
            try:
                # Use positive pressures only
                positive_mask = pressure_clean > 0
                if np.sum(positive_mask) > 2:
                    # Handle both pandas Series and numpy arrays
                    if hasattr(pressure_clean, 'iloc'):
                        pressure_subset = pressure_clean[positive_mask]
                        time_subset = time_seconds[positive_mask]
                    else:
                        pressure_subset = pressure_clean[positive_mask]
                        time_subset = time_seconds[positive_mask]
                    
                    log_pressure = np.log(pressure_subset)
                    
                    coeffs_exp = np.polyfit(time_subset, log_pressure, 1)
                    exp_leak_rate = coeffs_exp[0] * np.mean(pressure_clean)
                    exp_fit_quality = np.corrcoef(log_pressure, 
                                                np.polyval(coeffs_exp, time_subset))[0, 1] ** 2
                    
                    # Time constant
                    time_constant = -1 / coeffs_exp[0] if coeffs_exp[0] != 0 else np.inf
                    
                    results['exponential'] = {
                        'leak_rate': abs(exp_leak_rate),
                        'fit_quality': exp_fit_quality,
                        'time_constant': time_constant,
                        'units': 'mbar/s'
                    }
                else:
                    results['exponential'] = {'leak_rate': 0, 'fit_quality': 0, 'time_constant': np.inf, 'units': 'mbar/s'}
            except Exception as e:
                logger.warning(f"Exponential fit failed: {e}")
                results['exponential'] = {'leak_rate': 0, 'fit_quality': 0, 'time_constant': np.inf, 'units': 'mbar/s'}

            # Method 3: Conductance-based leak rate (for known system volume)
            try:
                # Estimate based on pressure rise rate and typical volumes
                if hasattr(time_seconds, 'iloc'):
                    dt = time_seconds.iloc[-1] - time_seconds.iloc[0]
                else:
                    dt = time_seconds[-1] - time_seconds[0]
                
                if hasattr(pressure_clean, 'iloc'):
                    dp = pressure_clean.iloc[-1] - pressure_clean.iloc[0]
                else:
                    dp = pressure_clean[-1] - pressure_clean[0]
                
                dp_dt = dp / dt if dt != 0 else 0
                
                # Typical vacuum chamber volumes (1-1000 L)
                volumes = [1, 10, 100, 1000]  # liters
                conductance_rates = {}
                
                for vol in volumes:
                    # Q = V * dP/dt (for molecular flow regime)
                    conductance_leak_rate = vol * dp_dt * 1e-3  # mbar⋅L/s
                    conductance_rates[f'{vol}L'] = {
                        'leak_rate': conductance_leak_rate,
                        'units': 'mbar⋅L/s'
                    }
                
                results['conductance'] = conductance_rates
            except:
                results['conductance'] = {}

            # Overall assessment
            primary_method = 'exponential' if results.get('exponential', {}).get('fit_quality', 0) > 0.8 else 'linear'
            primary_leak_rate = results.get(primary_method, {}).get('leak_rate', 0)
            
            # Classify leak severity
            if primary_leak_rate > 1e-6:
                severity = 'severe'
            elif primary_leak_rate > 1e-8:
                severity = 'significant'
            elif primary_leak_rate > 1e-10:
                severity = 'minor'
            else:
                severity = 'negligible'

            results['summary'] = {
                'primary_method': primary_method,
                'leak_rate': primary_leak_rate,
                'severity': severity,
                'start_pressure': start_pressure,
                'end_pressure': end_pressure,
                'total_rise': end_pressure - start_pressure,
                'analysis_duration': time_seconds.iloc[-1] if len(time_seconds) > 0 else 0
            }

            return results
            
        except Exception as e:
            logger.error(f"Error in leak rate calculation: {e}")
            return {}

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
        try:
            if len(pressure_data) < 2 or len(time_data) < 2:
                return {}
                
            # Clean data
            mask = ~(pd.isna(pressure_data) | pd.isna(time_data))
            pressure_clean = pressure_data[mask]
            time_clean = time_data[mask]
            
            if len(pressure_clean) < 2:
                return {}
            
            initial_pressure = pressure_clean[0]
            final_pressure = pressure_clean[-1]

            # Enhanced milestone calculation
            milestones = {}
            pressure_targets = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9]

            for target in pressure_targets:
                if final_pressure <= target < initial_pressure:
                    idx = np.where(pressure_clean <= target)[0]
                    if len(idx) > 0:
                        time_to_target = time_clean[idx[0]] - time_clean[0]
                        # Handle datetime objects
                        if hasattr(time_to_target, 'total_seconds'):
                            time_to_target = time_to_target.total_seconds()
                        milestones[f"{target:.0e} mbar"] = {
                            'time': time_clean[idx[0]], 
                            'duration': time_to_target,
                            'index': idx[0]
                        }

            # Calculate pumping characteristics
            log_pressure = np.log10(pressure_clean)
            d_log_p_dt = np.gradient(log_pressure)
            
            # Find pump-down rate phases
            pump_rates = []
            window_size = max(10, len(pressure_clean) // 20)
            
            for i in range(0, len(pressure_clean) - window_size, window_size // 2):
                window_pressure = pressure_clean[i:i + window_size]
                window_time = time_clean[i:i + window_size]
                
                # Calculate pump rate for this window
                if len(window_pressure) > 2:
                    try:
                        # Convert time to seconds if datetime
                        if hasattr(window_time[0], 'timestamp'):
                            time_sec = np.array([t.timestamp() for t in window_time])
                        else:
                            time_sec = window_time
                            
                        # Linear fit to log pressure vs time
                        coeffs = np.polyfit(time_sec - time_sec[0], np.log(window_pressure), 1)
                        pump_rate = -coeffs[0]  # Negative slope = pump-down rate
                        
                        pump_rates.append({
                            'start_time': window_time[0],
                            'pressure_range': (window_pressure[0], window_pressure[-1]),
                            'pump_rate': pump_rate,
                            'effective_speed': pump_rate * np.mean(window_pressure)
                        })
                    except:
                        continue
            
            # Calculate ultimate vacuum and time constant
            try:
                # Fit exponential decay to entire curve
                if hasattr(time_clean[0], 'timestamp'):
                    time_numeric = np.array([t.timestamp() for t in time_clean])
                    time_numeric = time_numeric - time_numeric[0]
                else:
                    time_numeric = time_clean - time_clean[0]
                    
                # Exponential fit: P(t) = P0 * exp(-t/tau) + P_ultimate
                from scipy.optimize import curve_fit
                
                def exp_decay(t, p0, tau, p_ult):
                    return p0 * np.exp(-t / tau) + p_ult
                
                try:
                    popt, pcov = curve_fit(exp_decay, time_numeric, pressure_clean, 
                                         p0=[initial_pressure, 100, final_pressure],
                                         bounds=([0, 1, 0], [np.inf, np.inf, initial_pressure]))
                    
                    time_constant = popt[1]
                    ultimate_vacuum = popt[2]
                    fit_quality = np.corrcoef(pressure_clean, 
                                            exp_decay(time_numeric, *popt))[0, 1] ** 2
                except:
                    time_constant = None
                    ultimate_vacuum = final_pressure
                    fit_quality = 0
                    
            except:
                time_constant = None
                ultimate_vacuum = final_pressure
                fit_quality = 0

            return {
                'initial_pressure': initial_pressure,
                'final_pressure': final_pressure,
                'ultimate_vacuum': ultimate_vacuum,
                'pressure_drop_ratio': initial_pressure / final_pressure if final_pressure > 0 else float('inf'),
                'milestones': milestones,
                'pumping_speed_indicator': -d_log_p_dt,
                'pump_rates': pump_rates,
                'time_constant': time_constant,
                'fit_quality': fit_quality,
                'total_pump_time': time_clean[-1] - time_clean[0] if len(time_clean) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in pump-down analysis: {e}")
            return {}

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
        try:
            # Clean data
            mask = ~(pd.isna(pressure_data) | pd.isna(time_data))
            pressure_clean = pressure_data[mask]
            time_clean = time_data[mask]
            
            if len(pressure_clean) < 2:
                return {}

            # Convert time to seconds if needed
            if pd.api.types.is_datetime64_any_dtype(time_clean):
                time_seconds = (time_clean - time_clean.iloc[0]).dt.total_seconds()
            else:
                time_seconds = time_clean - time_clean[0]

            # Calculate pressure rise rate
            dp_dt = np.gradient(pressure_clean, time_seconds)
            
            # Outgassing rate Q = V * dP/dt
            outgassing_rates = volume_liters * dp_dt  # mbar⋅L/s
            
            # Average outgassing rate
            avg_outgassing_rate = np.mean(outgassing_rates)
            
            # Outgassing per unit area (assuming 1 m² surface area)
            surface_area_m2 = 1.0  # Default assumption
            specific_outgassing = avg_outgassing_rate / surface_area_m2  # mbar⋅L/(s⋅m²)
            
            # Classify outgassing level
            if avg_outgassing_rate > 1e-6:
                level = 'high'
            elif avg_outgassing_rate > 1e-8:
                level = 'moderate'
            elif avg_outgassing_rate > 1e-10:
                level = 'low'
            else:
                level = 'very_low'

            return {
                'outgassing_rate': outgassing_rates,
                'average_rate': avg_outgassing_rate,
                'specific_outgassing': specific_outgassing,
                'level': level,
                'volume': volume_liters,
                'units': 'mbar⋅L/s'
            }
            
        except Exception as e:
            logger.error(f"Error in outgassing calculation: {e}")
            return {}

    @staticmethod
    def detect_pump_down_cycles(pressure_data, time_data, min_pressure_drop=2.0, min_duration=10):
        """
        Detect pump-down cycles in vacuum data
        
        Args:
            pressure_data: Array of pressure values
            time_data: Array of time values
            min_pressure_drop: Minimum pressure drop (orders of magnitude)
            min_duration: Minimum cycle duration (data points)
            
        Returns:
            list: List of detected pump-down cycles
        """
        try:
            # Clean data and ensure consistent types
            mask = ~(pd.isna(pressure_data) | pd.isna(time_data))
            pressure_clean = pressure_data[mask]
            time_clean = time_data[mask]
            
            # Convert to pandas Series for consistent handling
            if not isinstance(pressure_clean, pd.Series):
                pressure_clean = pd.Series(pressure_clean)
            if not isinstance(time_clean, pd.Series):
                time_clean = pd.Series(time_clean)
            
            if len(pressure_clean) < min_duration:
                return []

            # Calculate pressure derivative on log scale
            log_pressure = np.log10(pressure_clean + 1e-12)  # Avoid log(0)
            d_log_p_dt = np.gradient(log_pressure)
            
            # Identify pump-down regions (negative derivative)
            pump_threshold = -0.001  # Threshold for pump-down detection
            pump_mask = d_log_p_dt < pump_threshold
            
            cycles = []
            cycle_start = None
            
            for i in range(len(pump_mask)):
                if pump_mask[i] and cycle_start is None:
                    cycle_start = i
                elif not pump_mask[i] and cycle_start is not None:
                    cycle_duration = i - cycle_start
                    
                    if cycle_duration >= min_duration:
                        # Analyze this cycle
                        cycle_pressure = pressure_clean.iloc[cycle_start:i]
                        cycle_time = time_clean.iloc[cycle_start:i]
                        
                        p_initial = cycle_pressure.iloc[0]
                        p_final = cycle_pressure.iloc[-1]
                        
                        if p_initial > 0 and p_final > 0:
                            pressure_drop = np.log10(p_initial / p_final)
                            
                            if pressure_drop >= min_pressure_drop:
                                # Calculate pump-down characteristics
                                pump_time = cycle_time.iloc[-1] - cycle_time.iloc[0]
                                if hasattr(pump_time, 'total_seconds'):
                                    pump_time = pump_time.total_seconds()
                                
                                # Pumping speed estimate
                                if pump_time > 0:
                                    avg_pump_speed = pressure_drop / pump_time
                                else:
                                    avg_pump_speed = 0
                                
                                cycles.append({
                                    'start_index': cycle_start,
                                    'end_index': i,
                                    'start_time': cycle_time.iloc[0],
                                    'end_time': cycle_time.iloc[-1],
                                    'duration': pump_time,
                                    'initial_pressure': p_initial,
                                    'final_pressure': p_final,
                                    'pressure_drop': pressure_drop,
                                    'avg_pump_speed': avg_pump_speed,
                                    'efficiency': 'high' if pressure_drop > 4 else 'moderate' if pressure_drop > 2 else 'low'
                                })
                    
                    cycle_start = None
            
            return cycles
            
        except Exception as e:
            logger.error(f"Error in pump-down cycle detection: {e}")
            return []

    @staticmethod
    def calculate_base_pressure(pressure_data, percentile=10):
        """
        Calculate the base pressure from vacuum data
        
        Args:
            pressure_data: Array of pressure values
            percentile: Percentile to use for base pressure calculation
            
        Returns:
            float: Base pressure value
        """
        try:
            # Clean data
            pressure_clean = pd.Series(pressure_data).dropna()
            if len(pressure_clean) < 2:
                return 0
            
            # Use the specified percentile as base pressure
            base_pressure = np.percentile(pressure_clean, percentile)
            return base_pressure
            
        except Exception as e:
            logger.error(f"Error in base pressure calculation: {e}")
            return 0

    @staticmethod
    def analyze_vacuum_system_performance(pressure_data, time_data, system_volume=None):
        """
        Comprehensive vacuum system performance analysis
        
        Args:
            pressure_data: Array of pressure values
            time_data: Array of time values
            system_volume: System volume in liters (optional)
            
        Returns:
            dict: Comprehensive performance metrics
        """
        try:
            # Clean data and ensure consistent types
            mask = ~(pd.isna(pressure_data) | pd.isna(time_data))
            pressure_clean = pressure_data[mask]
            time_clean = time_data[mask]
            
            # Convert to pandas Series for consistent handling
            if not isinstance(pressure_clean, pd.Series):
                pressure_clean = pd.Series(pressure_clean)
            if not isinstance(time_clean, pd.Series):
                time_clean = pd.Series(time_clean)
            
            if len(pressure_clean) < 10:
                return {}

            results = {}
            
            # Basic metrics
            results['basic_metrics'] = {
                'min_pressure': pressure_clean.min(),
                'max_pressure': pressure_clean.max(),
                'mean_pressure': pressure_clean.mean(),
                'pressure_stability': pressure_clean.std() / pressure_clean.mean(),
                'data_points': len(pressure_clean)
            }
            
            # Detect different operational phases
            # 1. Base pressure regions (stable low pressure)
            base_pressure = VacuumAnalysisTools.calculate_base_pressure(pressure_clean)
            results['base_pressure'] = base_pressure
            
            # 2. Pump-down cycles
            pump_cycles = VacuumAnalysisTools.detect_pump_down_cycles(pressure_clean, time_clean)
            results['pump_cycles'] = pump_cycles
            
            # 3. Pressure spikes
            spikes = VacuumAnalysisTools.detect_pressure_spikes(pressure_clean)
            results['pressure_spikes'] = spikes
            
            # 4. Leak rate analysis (if rising pressure periods found)
            if len(pressure_clean) > 50:
                # Look for periods of rising pressure
                d_p_dt = np.gradient(pressure_clean)
                rising_mask = d_p_dt > np.percentile(d_p_dt, 75)
                
                if np.sum(rising_mask) > 10:
                    rising_indices = np.where(rising_mask)[0]
                    # Use the indices to get a subset for leak analysis
                    leak_pressure = pressure_clean.iloc[rising_indices]
                    leak_time = time_clean.iloc[rising_indices]
                    leak_analysis = VacuumAnalysisTools.calculate_leak_rate(
                        leak_pressure,
                        leak_time,
                        leak_pressure.iloc[0] if len(leak_pressure) > 0 else 0
                    )
                    results['leak_analysis'] = leak_analysis
            
            # 5. System volume estimation (if not provided)
            if system_volume is None:
                # Estimate from pump-down characteristics
                if pump_cycles:
                    # Use first pump cycle for estimation
                    cycle = pump_cycles[0]
                    estimated_volume = 10  # Default 10L assumption
                    results['estimated_volume'] = estimated_volume
                else:
                    estimated_volume = 10
                    results['estimated_volume'] = estimated_volume
            else:
                estimated_volume = system_volume
                results['system_volume'] = system_volume
            
            # 6. Overall system rating
            rating_score = 0
            rating_factors = []
            
            # Base pressure quality (lower is better)
            if base_pressure < 1e-8:
                rating_score += 20
                rating_factors.append("Excellent base pressure")
            elif base_pressure < 1e-6:
                rating_score += 15
                rating_factors.append("Good base pressure")
            elif base_pressure < 1e-4:
                rating_score += 10
                rating_factors.append("Adequate base pressure")
            else:
                rating_factors.append("Poor base pressure")
            
            # Pump-down efficiency
            if pump_cycles:
                avg_efficiency = np.mean([c.get('pressure_drop', 0) for c in pump_cycles])
                if avg_efficiency > 5:
                    rating_score += 20
                    rating_factors.append("Excellent pump-down efficiency")
                elif avg_efficiency > 3:
                    rating_score += 15
                    rating_factors.append("Good pump-down efficiency")
                elif avg_efficiency > 1:
                    rating_score += 10
                    rating_factors.append("Adequate pump-down efficiency")
                else:
                    rating_factors.append("Poor pump-down efficiency")
            
            # Spike frequency (fewer is better)
            spike_rate = len(spikes) / len(pressure_clean) * 1000  # spikes per 1000 points
            if spike_rate < 1:
                rating_score += 20
                rating_factors.append("Low spike frequency")
            elif spike_rate < 5:
                rating_score += 15
                rating_factors.append("Moderate spike frequency")
            elif spike_rate < 10:
                rating_score += 10
                rating_factors.append("High spike frequency")
            else:
                rating_factors.append("Very high spike frequency")
            
            # Pressure stability
            stability = results['basic_metrics']['pressure_stability']
            if stability < 0.1:
                rating_score += 20
                rating_factors.append("Excellent pressure stability")
            elif stability < 0.3:
                rating_score += 15
                rating_factors.append("Good pressure stability")
            elif stability < 0.5:
                rating_score += 10
                rating_factors.append("Adequate pressure stability")
            else:
                rating_factors.append("Poor pressure stability")
            
            # Overall grade
            if rating_score >= 70:
                grade = 'A'
                performance = 'Excellent'
            elif rating_score >= 50:
                grade = 'B'
                performance = 'Good'
            elif rating_score >= 30:
                grade = 'C'
                performance = 'Adequate'
            else:
                grade = 'D'
                performance = 'Poor'
            
            results['system_rating'] = {
                'score': rating_score,
                'grade': grade,
                'performance': performance,
                'factors': rating_factors
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vacuum system performance analysis: {e}")
            return {}
