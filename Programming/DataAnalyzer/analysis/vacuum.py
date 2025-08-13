#!/usr/bin/env python3
"""
Vacuum-specific analysis tools - FIXED VERSION
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class VacuumAnalyzer:
    """Fixed Vacuum analysis tools (no self in static methods)"""

    @staticmethod
    def calculate_base_pressure(pressure_data: np.ndarray,
                               window_minutes: float = 10,
                               sample_rate_hz: float = 1.0) -> float:
        """Calculate base pressure"""
        window_samples = max(1, min(
            int(window_minutes * 60 * sample_rate_hz),
            len(pressure_data)
        ))
        pressure_series = pd.Series(pressure_data)
        rolling_min = pressure_series.rolling(window=window_samples, center=True).min()
        rolling_std = pressure_series.rolling(window=window_samples, center=True).std()

        if rolling_std.empty:
            base_pressure = np.nanmin(pressure_data)
        else:
            most_stable_idx = rolling_std.idxmin()
            base_pressure = rolling_min.iloc[most_stable_idx]

        return float(base_pressure) if not np.isnan(base_pressure) else 1e-6

    @staticmethod
    def calculate_leak_rate(pressure_data: np.ndarray,
                           time_data: np.ndarray,
                           volume_liters: float = 1.0) -> float:
        """Calculate leak rate"""
        mask = ~(np.isnan(pressure_data) | np.isnan(time_data))
        pressure_clean = pressure_data[mask]
        time_clean = time_data[mask]

        if len(pressure_clean) < 2:
            return 0.0

        try:
            pressure_positive = np.maximum(pressure_clean, 1e-10)
            log_pressure = np.log(pressure_positive)
            coeffs = np.polyfit(time_clean, log_pressure, 1)
            slope = coeffs[0]
            leak_rate = volume_liters * slope * np.mean(pressure_clean)
            return abs(float(leak_rate))
        except Exception:
            return 0.0

    @staticmethod
    def detect_pressure_spikes(pressure_data: np.ndarray,
                              threshold_sigma: float = 3.0,
                              min_duration: int = 1) -> List[int]:
        """Detect pressure spikes - returns list of indices"""
        spike_indices = []
        window = min(100, len(pressure_data) // 10)
        pressure_series = pd.Series(pressure_data)

        rolling_mean = pressure_series.rolling(window=window, center=True).mean()
        rolling_mean = rolling_mean.bfill().ffill()

        rolling_std = pressure_series.rolling(window=window, center=True).std()
        rolling_std = rolling_std.bfill().ffill()

        threshold = rolling_mean + threshold_sigma * rolling_std
        spike_mask = pressure_data > threshold

        in_spike = False
        spike_start = None

        for i, is_spike in enumerate(spike_mask):
            if is_spike and not in_spike:
                spike_start = i
                in_spike = True
            elif not is_spike and in_spike:
                if i - spike_start >= min_duration:
                    for idx in range(spike_start, i):
                        spike_indices.append(idx)
                in_spike = False
                spike_start = None

        if in_spike and spike_start is not None:
            if len(pressure_data) - spike_start >= min_duration:
                for idx in range(spike_start, len(pressure_data)):
                    spike_indices.append(idx)

        return spike_indices

    def detect_spikes(self, pressure_data: np.ndarray, threshold_sigma: float = 3.0, time_data: np.ndarray = None) -> List[dict]:
        """Instance method wrapper for spike detection"""
        spike_indices = self.detect_pressure_spikes(pressure_data, threshold_sigma)
        
        # Convert indices to spike objects with properties
        spikes = []
        if time_data is None:
            time_data = np.arange(len(pressure_data), dtype=float)
        
        # Group consecutive indices into spike events
        if spike_indices:
            spike_groups = []
            current_group = [spike_indices[0]]
            
            for i in range(1, len(spike_indices)):
                if spike_indices[i] == spike_indices[i-1] + 1:
                    current_group.append(spike_indices[i])
                else:
                    spike_groups.append(current_group)
                    current_group = [spike_indices[i]]
            spike_groups.append(current_group)
            
            # Create spike objects
            for group in spike_groups:
                start_idx = group[0]
                end_idx = group[-1]
                
                spike_data = {
                    'start_time': float(time_data[start_idx]),
                    'end_time': float(time_data[end_idx]),
                    'duration': float(time_data[end_idx] - time_data[start_idx]),
                    'max_pressure': float(np.max(pressure_data[start_idx:end_idx+1])),
                    'severity': 'High' if len(group) > 10 else 'Medium' if len(group) > 5 else 'Low',
                    'indices': group
                }
                spikes.append(spike_data)
        
        return spikes

    def detect_leaks(self, pressure_data: np.ndarray, time_data: np.ndarray = None, volume_liters: float = 1.0) -> float:
        """Instance method wrapper for leak detection"""
        if time_data is None:
            # Create synthetic time data if not provided
            time_data = np.arange(len(pressure_data), dtype=float)
        return self.calculate_leak_rate(pressure_data, time_data, volume_liters)

    def analyze_pumpdown(self, pressure_data: np.ndarray, time_data: np.ndarray = None) -> dict:
        """Analyze pumpdown performance and characteristics"""
        try:
            if time_data is None:
                time_data = np.arange(len(pressure_data), dtype=float)
            
            # Calculate base pressure
            base_pressure = self.calculate_base_pressure(pressure_data)
            
            # Calculate leak rate
            leak_rate = self.calculate_leak_rate(pressure_data, time_data)
            
            # Find pumpdown phases
            pressure_diff = np.diff(pressure_data)
            pumpdown_mask = pressure_diff < 0
            
            # Calculate pumpdown rate (pressure drop per unit time)
            pumpdown_indices = np.where(pumpdown_mask)[0]
            if len(pumpdown_indices) > 0:
                pumpdown_rate = np.mean(np.abs(pressure_diff[pumpdown_indices]))
            else:
                pumpdown_rate = 0.0
            
            # Calculate time to reach certain pressure levels
            initial_pressure = float(pressure_data[0])
            min_pressure = float(np.min(pressure_data))
            
            # Time to reach 10% of initial pressure
            target_10_percent = initial_pressure * 0.1
            time_to_10_percent = None
            for i, p in enumerate(pressure_data):
                if p <= target_10_percent:
                    time_to_10_percent = float(time_data[i])
                    break
            
            # Time to reach minimum pressure
            min_pressure_index = np.argmin(pressure_data)
            time_to_min = float(time_data[min_pressure_index])
            
            # Calculate pumping efficiency
            pressure_range = initial_pressure - min_pressure
            time_range = time_to_min - time_data[0]
            if time_range > 0:
                pumping_efficiency = pressure_range / time_range
            else:
                pumping_efficiency = 0.0
            
            return {
                'base_pressure': base_pressure,
                'leak_rate': leak_rate,
                'pumpdown_rate': pumpdown_rate,
                'initial_pressure': initial_pressure,
                'min_pressure': min_pressure,
                'time_to_10_percent': time_to_10_percent,
                'time_to_min': time_to_min,
                'pumping_efficiency': pumping_efficiency,
                'pressure_range': pressure_range
            }
            
        except Exception as e:
            logging.warning(f"Pumpdown analysis failed: {e}")
            return {
                'base_pressure': 0.0,
                'leak_rate': 0.0,
                'pumpdown_rate': 0.0,
                'initial_pressure': 0.0,
                'min_pressure': 0.0,
                'time_to_10_percent': None,
                'time_to_min': 0.0,
                'pumping_efficiency': 0.0,
                'pressure_range': 0.0
            }
