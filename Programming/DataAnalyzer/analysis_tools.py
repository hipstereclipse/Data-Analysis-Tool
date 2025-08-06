#!/usr/bin/env python3
"""
analysis_tools.py - Data analysis and vacuum-specific analysis tools
Contains methods for analyzing data series and performing vacuum pressure calculations
"""

import numpy as np  # For numerical operations
import pandas as pd  # For data manipulation
from scipy import stats  # For statistical functions
from scipy.signal import find_peaks, savgol_filter  # For signal processing
from scipy.interpolate import make_interp_spline  # For interpolation
from sklearn.linear_model import LinearRegression  # For linear regression
from sklearn.ensemble import IsolationForest  # For outlier detection
from sklearn.neighbors import LocalOutlierFactor  # For local outlier detection
from sklearn.preprocessing import StandardScaler  # For data scaling
from sklearn.decomposition import PCA  # For principal component analysis


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
        # Initialize statistics dictionary
        stats_dict = {
            'count': len(data),  # Number of data points
            'mean': np.mean(data),  # Average value
            'median': np.median(data),  # Middle value
            'std': np.std(data),  # Standard deviation
            'var': np.var(data),  # Variance
            'min': np.min(data),  # Minimum value
            'max': np.max(data),  # Maximum value
            'range': np.max(data) - np.min(data),  # Data range
            'q1': np.percentile(data, 25),  # First quartile
            'q3': np.percentile(data, 75),  # Third quartile
            'iqr': np.percentile(data, 75) - np.percentile(data, 25),  # Interquartile range
            'skewness': stats.skew(data),  # Measure of asymmetry
            'kurtosis': stats.kurtosis(data),  # Measure of tail heaviness
            'cv': np.std(data) / np.mean(data) if np.mean(data) != 0 else np.nan  # Coefficient of variation
        }
        return stats_dict

    @staticmethod
    def find_peaks_and_valleys(x_data, y_data, prominence=None):
        """
        Find peaks (maxima) and valleys (minima) in the data

        Args:
            x_data: X-axis values
            y_data: Y-axis values
            prominence: Minimum prominence of peaks (height relative to neighbors)

        Returns:
            dict: Dictionary with peak and valley information
        """
        # Find peaks (local maxima)
        peaks, peak_props = find_peaks(y_data, prominence=prominence)

        # Find valleys by inverting data and finding peaks
        valleys, valley_props = find_peaks(-y_data, prominence=prominence)

        # Return organized results
        return {
            'peaks': {
                'indices': peaks,  # Array indices of peaks
                'x_values': x_data[peaks],  # X coordinates of peaks
                'y_values': y_data[peaks]  # Y values at peaks
            },
            'valleys': {
                'indices': valleys,  # Array indices of valleys
                'x_values': x_data[valleys],  # X coordinates of valleys
                'y_values': y_data[valleys]  # Y values at valleys
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
        # Use pandas rolling window with center alignment
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
        # Use numpy gradient for numerical differentiation
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
        # Compute FFT
        fft_values = np.fft.fft(data)

        # Compute frequency bins
        frequencies = np.fft.fftfreq(len(data), 1 / sample_rate)

        # Return only positive frequencies
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
        # Use pandas correlation method
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
        # Reshape x_data for sklearn
        x_data = np.array(x_data).reshape(-1, 1)
        y_data = np.array(y_data)

        if degree == 1:
            # Linear regression using sklearn
            model = LinearRegression()
            model.fit(x_data, y_data)
            y_pred = model.predict(x_data)
            r2 = model.score(x_data, y_data)
            coefficients = [model.intercept_, model.coef_[0]]
        else:
            # Polynomial regression using numpy
            coefficients = np.polyfit(x_data.flatten(), y_data, degree)
            poly = np.poly1d(coefficients)
            y_pred = poly(x_data.flatten())

            # Calculate R-squared manually
            ss_res = np.sum((y_data - y_pred) ** 2)
            ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
            r2 = 1 - (ss_res / ss_tot)

        # Return comprehensive results
        return {
            'coefficients': coefficients,  # Regression coefficients
            'y_predicted': y_pred,  # Predicted values
            'r_squared': r2,  # Coefficient of determination
            'residuals': y_data - y_pred  # Prediction errors
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
            # Interquartile range method
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outliers = (data < lower_bound) | (data > upper_bound)

        elif method == 'zscore':
            # Z-score method
            z_scores = np.abs(stats.zscore(data))
            outliers = z_scores > threshold

        elif method == 'isolation':
            # Isolation Forest method
            clf = IsolationForest(contamination=0.1, random_state=42)
            outliers = clf.fit_predict(data.reshape(-1, 1)) == -1

        else:
            # Default to no outliers
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
        Finds the most stable low-pressure region

        Args:
            pressure_data: Array of pressure values
            window_minutes: Size of analysis window in minutes
            sample_rate_hz: Data sampling rate in Hz

        Returns:
            tuple: (base_pressure, rolling_min, rolling_std)
        """
        # Convert window size to number of samples
        window_size = int(window_minutes * 60 * sample_rate_hz)

        # Calculate rolling minimum (lowest pressure in each window)
        rolling_min = pd.Series(pressure_data).rolling(window=window_size, center=True).min()

        # Calculate rolling standard deviation (pressure stability)
        rolling_std = pd.Series(pressure_data).rolling(window=window_size, center=True).std()

        # Find base pressure from the most stable region
        if not rolling_std.isna().all():
            # Find index of minimum standard deviation (most stable)
            most_stable_idx = rolling_std.idxmin()
            # Base pressure is the minimum at that stable point
            base_pressure = rolling_min.iloc[most_stable_idx]
        else:
            # Fallback to overall minimum
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
        # Remove trend using 2nd order polynomial fit
        x = np.arange(len(pressure_data))
        coeffs = np.polyfit(x, pressure_data, 2)
        trend = np.polyval(coeffs, x)
        detrended = pressure_data - trend

        # Calculate noise metrics
        noise_rms = np.sqrt(np.mean(detrended ** 2))  # Root mean square noise
        noise_peak_to_peak = np.max(detrended) - np.min(detrended)  # Peak-to-peak noise

        # Frequency analysis using FFT
        fft_values = np.fft.fft(detrended)
        frequencies = np.fft.fftfreq(len(detrended), 1 / sample_rate_hz)
        power_spectrum = np.abs(fft_values) ** 2

        # Find dominant noise frequency
        positive_freq_mask = frequencies > 0
        if np.any(positive_freq_mask):
            dominant_freq_idx = np.argmax(power_spectrum[positive_freq_mask])
            dominant_frequency = frequencies[positive_freq_mask][dominant_freq_idx]
        else:
            dominant_frequency = 0

        return {
            'noise_rms': noise_rms,  # RMS noise level
            'noise_p2p': noise_peak_to_peak,  # Peak-to-peak noise
            'dominant_freq': dominant_frequency,  # Dominant noise frequency
            'power_spectrum': power_spectrum[positive_freq_mask],  # Power spectrum
            'frequencies': frequencies[positive_freq_mask],  # Frequency bins
            'detrended_signal': detrended  # Detrended signal
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
        # Calculate rolling statistics for adaptive threshold
        rolling_mean = pd.Series(pressure_data).rolling(window=100, center=True).mean()
        rolling_std = pd.Series(pressure_data).rolling(window=100, center=True).std()

        # Define spike threshold
        threshold = rolling_mean + threshold_factor * rolling_std

        # Identify points above threshold
        spike_mask = pressure_data > threshold

        # Group consecutive spike points
        spikes = []
        spike_start = None

        for i, is_spike in enumerate(spike_mask):
            if is_spike and spike_start is None:
                # Start of new spike
                spike_start = i
            elif not is_spike and spike_start is not None:
                # End of spike
                duration = i - spike_start
                if duration >= min_spike_duration:
                    # Valid spike found
                    max_pressure = np.max(pressure_data[spike_start:i])
                    # Classify severity
                    severity = 'high' if max_pressure > rolling_mean.iloc[spike_start] * 10 else 'medium'

                    spikes.append({
                        'start': spike_start,  # Start index
                        'end': i,  # End index
                        'duration': duration,  # Duration in points
                        'max_pressure': max_pressure,  # Peak pressure
                        'severity': severity  # Severity classification
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
            end_pressure: Final pressure (default: last value)

        Returns:
            dict: Dictionary containing leak rate analysis
        """
        # Use final pressure if not specified
        if end_pressure is None:
            end_pressure = pressure_data[-1]

        # Convert time to seconds if datetime
        if pd.api.types.is_datetime64_any_dtype(time_data):
            time_seconds = (time_data - time_data.iloc[0]).dt.total_seconds()
        else:
            time_seconds = time_data

        # Fit exponential model (linear in log space)
        log_pressure = np.log(pressure_data)
        coeffs = np.polyfit(time_seconds, log_pressure, 1)

        # Calculate leak rate (approximate, in mbar·L/s)
        leak_rate = coeffs[0] * np.mean(pressure_data)

        # Generate fitted curve
        fitted = np.exp(np.polyval(coeffs, time_seconds))

        # Calculate quality of fit (R-squared)
        ss_res = np.sum((pressure_data - fitted) ** 2)
        ss_tot = np.sum((pressure_data - np.mean(pressure_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Calculate time constant
        time_constant = -1 / coeffs[0] if coeffs[0] != 0 else np.inf

        return {
            'leak_rate': leak_rate,  # Leak rate in mbar·L/s
            'r_squared': r_squared,  # Fit quality
            'fitted_curve': fitted,  # Fitted pressure curve
            'time_constant': time_constant  # Exponential time constant
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
        # Get initial and final pressures
        initial_pressure = pressure_data[0]
        final_pressure = pressure_data[-1]

        # Define pressure milestones to track
        milestones = {}
        pressure_targets = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]  # Common vacuum levels

        # Find time to reach each milestone
        for target in pressure_targets:
            if final_pressure <= target < initial_pressure:
                # Find first point below target
                idx = np.where(pressure_data <= target)[0]
                if len(idx) > 0:
                    milestones[f"{target:.0e} mbar"] = time_data[idx[0]]

        # Calculate pumping speed indicator (rate of pressure decrease)
        log_pressure = np.log10(pressure_data)
        d_log_p_dt = np.gradient(log_pressure)  # Rate of log pressure change

        return {
            'initial_pressure': initial_pressure,  # Starting pressure
            'final_pressure': final_pressure,  # Ending pressure
            'milestones': milestones,  # Time to reach pressure levels
            'pumping_speed_indicator': -d_log_p_dt  # Pumping speed indicator
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
        # Convert time to seconds
        if pd.api.types.is_datetime64_any_dtype(time_data):
            time_seconds = (time_data - time_data.iloc[0]).dt.total_seconds()
        else:
            time_seconds = np.array(time_data)

        # Calculate pressure rise rate (dP/dt)
        dp_dt = np.gradient(pressure_data, time_seconds)

        # Calculate outgassing rate Q = V * dP/dt
        outgassing_rate = volume_liters * dp_dt

        # Average outgassing rate
        avg_outgassing = np.mean(outgassing_rate)

        return {
            'outgassing_rate': outgassing_rate,  # Time-dependent outgassing
            'average_rate': avg_outgassing,  # Average outgassing rate
            'units': 'mbar·L/s'  # Units
        }