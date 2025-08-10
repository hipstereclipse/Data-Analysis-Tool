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
