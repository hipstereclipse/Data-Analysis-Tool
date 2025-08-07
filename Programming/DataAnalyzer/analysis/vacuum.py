#!/usr/bin/env python3
"""
Vacuum-specific analysis tools
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


class VacuumAnalyzer:
    """Vacuum system analysis tools"""

    @staticmethod
    def calculate_base_pressure(
            pressure_data: np.ndarray,
            window_minutes: float = 10,
            sample_rate_hz: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate base pressure with stability analysis

        Args:
            pressure_data: Pressure values
            window_minutes: Analysis window in minutes
            sample_rate_hz: Data sampling rate

        Returns:
            Dictionary with base pressure analysis
        """
        # Convert window to samples
        window_samples = int(window_minutes * 60 * sample_rate_hz)
        window_samples = max(1, min(window_samples, len(pressure_data)))

        # Calculate rolling statistics
        pressure_series = pd.Series(pressure_data)
        rolling_min = pressure_series.rolling(window=window_samples, center=True).min()
        rolling_std = pressure_series.rolling(window=window_samples, center=True).std()
        rolling_mean = pressure_series.rolling(window=window_samples, center=True).mean()

        # Find most stable region (minimum std)
        valid_std = rolling_std.dropna()
        if len(valid_std) > 0:
            most_stable_idx = valid_std.idxmin()
            base_pressure = rolling_min.iloc[most_stable_idx]
            stability = rolling_std.iloc[most_stable_idx]
        else:
            base_pressure = np.nanmin(pressure_data)
            stability = np.nanstd(pressure_data)

        # Calculate confidence
        if stability > 0:
            confidence = 1.0 / (1.0 + stability / base_pressure) if base_pressure > 0 else 0
        else:
            confidence = 1.0

        return {
            'base_pressure': float(base_pressure) if not np.isnan(base_pressure) else None,
            'stability': float(stability) if not np.isnan(stability) else None,
            'confidence': float(confidence),
            'window_minutes': window_minutes,
            'rolling_min': rolling_min.values,
            'rolling_std': rolling_std.values,
            'most_stable_index': int(most_stable_idx) if not np.isnan(most_stable_idx) else None
        }

    @staticmethod
    def detect_pressure_spikes(
            pressure_data: np.ndarray,
            threshold_sigma: float = 3.0,
            min_duration: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Detect pressure spikes in vacuum data

        Args:
            pressure_data: Pressure values
            threshold_sigma: Detection threshold in standard deviations
            min_duration: Minimum spike duration in samples

        Returns:
            List of spike events
        """
        spikes = []

        # Calculate adaptive threshold
        window = min(100, len(pressure_data) // 10)
        pressure_series = pd.Series(pressure_data)
        rolling_mean = pressure_series.rolling(window=window, center=True).mean().fillna(method='bfill').fillna(
            method='ffill')
        rolling_std = pressure_series.rolling(window=window, center=True).std().fillna(method='bfill').fillna(
            method='ffill')

        # Threshold for spike detection
        threshold = rolling_mean + threshold_sigma * rolling_std

        # Find spike regions
        spike_mask = pressure_data > threshold

        # Group consecutive spike points
        in_spike = False
        spike_start = None

        for i, is_spike in enumerate(spike_mask):
            if is_spike and not in_spike:
                # Start of spike
                spike_start = i
                in_spike = True

            elif not is_spike and in_spike:
                # End of spike
                if i - spike_start >= min_duration:
                    spike_region = pressure_data[spike_start:i]

                    spikes.append({
                        'start_index': spike_start,
                        'end_index': i,
                        'duration': i - spike_start,
                        'max_pressure': float(np.max(spike_region)),
                        'mean_pressure': float(np.mean(spike_region)),
                        'severity': VacuumAnalyzer._classify_spike_severity(
                            np.max(spike_region),
                            rolling_mean.iloc[spike_start]
                        )
                    })

                in_spike = False
                spike_start = None

        # Handle spike at end of data
        if in_spike and spike_start is not None:
            if len(pressure_data) - spike_start >= min_duration:
                spike_region = pressure_data[spike_start:]

                spikes.append({
                    'start_index': spike_start,
                    'end_index': len(pressure_data),
                    'duration': len(pressure_data) - spike_start,
                    'max_pressure': float(np.max(spike_region)),
                    'mean_pressure': float(np.mean(spike_region)),
                    'severity': VacuumAnalyzer._classify_spike_severity(
                        np.max(spike_region),
                        rolling_mean.iloc[spike_start]
                    )
                })

        return spikes

    @staticmethod
    def _classify_spike_severity(spike_max: float, baseline: float) -> str:
        """Classify spike severity"""
        if baseline <= 0:
            return 'unknown'

        ratio = spike_max / baseline

        if ratio > 100:
            return 'critical'
        elif ratio > 10:
            return 'high'
        elif ratio > 3:
            return 'medium'
        else:
            return 'low'

    @staticmethod
    def calculate_leak_rate(
            pressure_data: np.ndarray,
            time_data: np.ndarray,
            volume_liters: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate vacuum leak rate

        Args:
            pressure_data: Pressure values (mbar)
            time_data: Time values (seconds)
            volume_liters: System volume in liters

        Returns:
            Dictionary with leak rate analysis
        """
        # Clean data
        mask = ~(np.isnan(pressure_data) | np.isnan(time_data))
        pressure_clean = pressure_data[mask]
        time_clean = time_data[mask]

        if len(pressure_clean) < 2:
            return {
                'leak_rate': None,
                'leak_rate_unit': 'mbar·L/s',
                'r_squared': None,
                'confidence': 0
            }

        # Fit linear model to log pressure (exponential model)
        try:
            # Use log transform for exponential fit
            log_pressure = np.log(pressure_clean + 1e-10)  # Add small value to avoid log(0)

            # Linear regression on log pressure
            coeffs = np.polyfit(time_clean, log_pressure, 1)
            slope = coeffs[0]

            # Calculate leak rate (Q = V * dP/dt)
            leak_rate = volume_liters * slope * np.mean(pressure_clean)

            # Calculate R-squared
            fitted = np.polyval(coeffs, time_clean)
            ss_res = np.sum((log_pressure - fitted) ** 2)
            ss_tot = np.sum((log_pressure - np.mean(log_pressure)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Confidence based on R-squared and data quality
            confidence = r_squared * (1 - np.std(pressure_clean) / np.mean(pressure_clean))
            confidence = max(0, min(1, confidence))

            return {
                'leak_rate': float(leak_rate),
                'leak_rate_unit': 'mbar·L/s',
                'r_squared': float(r_squared),
                'confidence': float(confidence),
                'time_constant': -1 / slope if slope != 0 else np.inf,
                'fitted_values': np.exp(fitted).tolist()
            }

        except Exception as e:
            logger.error(f"Leak rate calculation failed: {e}")
            return {
                'leak_rate': None,
                'leak_rate_unit': 'mbar·L/s',
                'r_squared': None,
                'confidence': 0
            }

    @staticmethod
    def analyze_pump_down(
            pressure_data: np.ndarray,
            time_data: np.ndarray,
            target_pressure: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze pump-down characteristics

        Args:
            pressure_data: Pressure values during pump-down
            time_data: Time values
            target_pressure: Target base pressure

        Returns:
            Dictionary with pump-down analysis
        """
        # Clean data
        mask = ~(np.isnan(pressure_data) | np.isnan(time_data))
        pressure_clean = pressure_data[mask]
        time_clean = time_data[mask]

        if len(pressure_clean) < 2:
            return {
                'initial_pressure': None,
                'final_pressure': None,
                'pump_down_time': None,
                'pump_down_rate': None,
                'phases': []
            }

        initial_pressure = pressure_clean[0]
        final_pressure = pressure_clean[-1]

        # If no target specified, use 10% of initial or final pressure
        if target_pressure is None:
            target_pressure = min(final_pressure * 1.1, initial_pressure * 0.1)

        # Find time to reach target
        target_reached_idx = np.where(pressure_clean <= target_pressure)[0]
        if len(target_reached_idx) > 0:
            pump_down_time = time_clean[target_reached_idx[0]] - time_clean[0]
        else:
            pump_down_time = time_clean[-1] - time_clean[0]

        # Calculate average pump-down rate
        pump_down_rate = (initial_pressure - final_pressure) / (time_clean[-1] - time_clean[0])

        # Identify pump-down phases
        phases = VacuumAnalyzer._identify_pump_phases(pressure_clean, time_clean)

        return {
            'initial_pressure': float(initial_pressure),
            'final_pressure': float(final_pressure),
            'target_pressure': float(target_pressure),
            'pump_down_time': float(pump_down_time),
            'pump_down_rate': float(pump_down_rate),
            'phases': phases,
            'efficiency': float(final_pressure / initial_pressure)
        }

    @staticmethod
    def _identify_pump_phases(pressure: np.ndarray, time: np.ndarray) -> List[Dict[str, Any]]:
        """Identify different phases in pump-down curve"""
        phases = []

        # Calculate rate of change
        dp_dt = np.gradient(np.log(pressure + 1e-10), time)

        # Smooth the derivative
        if len(dp_dt) > 5:
            dp_dt_smooth = savgol_filter(dp_dt, min(5, len(dp_dt)), min(3, len(dp_dt) - 2))
        else:
            dp_dt_smooth = dp_dt

        # Find change points (where rate changes significantly)
        threshold = np.std(dp_dt_smooth) * 0.5
        change_points = []

        for i in range(1, len(dp_dt_smooth) - 1):
            if abs(dp_dt_smooth[i] - dp_dt_smooth[i - 1]) > threshold:
                change_points.append(i)

        # Define phases based on change points
        change_points = [0] + change_points + [len(pressure) - 1]

        for i in range(len(change_points) - 1):
            start_idx = change_points[i]
            end_idx = change_points[i + 1]

            phase_pressure = pressure[start_idx:end_idx]
            phase_time = time[start_idx:end_idx]

            if len(phase_pressure) > 1:
                phases.append({
                    'phase_number': i + 1,
                    'start_time': float(phase_time[0]),
                    'end_time': float(phase_time[-1]),
                    'start_pressure': float(phase_pressure[0]),
                    'end_pressure': float(phase_pressure[-1]),
                    'duration': float(phase_time[-1] - phase_time[0]),
                    'rate': float((phase_pressure[-1] - phase_pressure[0]) /
                                  (phase_time[-1] - phase_time[0])) if phase_time[-1] != phase_time[0] else 0
                })

        return phases

    @staticmethod
    def calculate_noise_metrics(
            pressure_data: np.ndarray,
            sample_rate_hz: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate noise characteristics in pressure data

        Args:
            pressure_data: Pressure values
            sample_rate_hz: Sampling rate

        Returns:
            Dictionary with noise metrics
        """
        # Remove trend
        x = np.arange(len(pressure_data))
        coeffs = np.polyfit(x, pressure_data, 2)
        trend = np.polyval(coeffs, x)
        detrended = pressure_data - trend

        # Calculate noise metrics
        noise_rms = np.sqrt(np.mean(detrended ** 2))
        noise_p2p = np.max(detrended) - np.min(detrended)

        # Calculate SNR
        signal_power = np.mean(pressure_data ** 2)
        noise_power = np.mean(detrended ** 2)
        snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else np.inf

        # Frequency analysis
        if len(detrended) > 2:
            fft_values = np.fft.fft(detrended)
            frequencies = np.fft.fftfreq(len(detrended), 1 / sample_rate_hz)
            power_spectrum = np.abs(fft_values) ** 2

            # Find dominant frequency
            positive_freq_mask = frequencies > 0
            if np.any(positive_freq_mask):
                dominant_freq_idx = np.argmax(power_spectrum[positive_freq_mask])
                dominant_frequency = frequencies[positive_freq_mask][dominant_freq_idx]
            else:
                dominant_frequency = 0
        else:
            dominant_frequency = 0

        return {
            'noise_rms': float(noise_rms),
            'noise_p2p': float(noise_p2p),
            'snr_db': float(snr_db),
            'dominant_frequency': float(dominant_frequency),
            'detrended_signal': detrended.tolist()
        }