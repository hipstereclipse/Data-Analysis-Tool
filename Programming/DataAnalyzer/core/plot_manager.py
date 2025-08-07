#!/usr/bin/env python3
"""
Plot generation and management
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
from scipy.interpolate import make_interp_spline

from models.data_models import FileData, SeriesConfig
from config.constants import PlotConfig, PlotTypes, MissingDataMethods, TrendTypes
from analysis.statistical import StatisticalAnalyzer
from utils.helpers import detect_datetime_axis

logger = logging.getLogger(__name__)


class PlotManager:
    """Manages plot creation and configuration"""

    def __init__(self):
        self.figure: Optional[Figure] = None
        self.axes: Optional[Any] = None
        self.current_config: Dict[str, Any] = {}
        self.color_cycle = plt.cm.tab10.colors

    def create_plot(
            self,
            series_list: List[SeriesConfig],
            files: Dict[str, FileData],
            config: Dict[str, Any]
    ) -> Figure:
        """Create plot from series configurations"""

        # Store configuration
        self.current_config = config

        # Create figure
        self.figure = Figure(
            figsize=(config.get('fig_width', PlotConfig.FIGURE_WIDTH),
                     config.get('fig_height', PlotConfig.FIGURE_HEIGHT)),
            dpi=config.get('dpi', PlotConfig.DPI)
        )

        # Apply theme
        self._apply_theme(config.get('theme', 'default'))

        # Create axes
        self.axes = self.figure.add_subplot(111)

        # Plot each series
        for i, series in enumerate(series_list):
            if not series.visible:
                continue

            file_data = files.get(series.file_id)
            if not file_data:
                logger.warning(f"File not found for series: {series.name}")
                continue

            try:
                self._plot_series(series, file_data, i)
            except Exception as e:
                logger.error(f"Failed to plot series {series.name}: {e}")

        # Configure axes
        self._configure_axes(config)

        # Add grid
        if config.get('show_grid', True):
            self._add_grid(config)

        # Add legend
        if config.get('show_legend', True):
            self._add_legend(config)

        # Apply layout
        self.figure.tight_layout()

        return self.figure

    def _plot_series(self, series: SeriesConfig, file_data: FileData, index: int):
        """Plot a single series"""

        # Get data
        x_data, y_data = series.get_data(file_data)

        # Handle missing data
        x_data, y_data = self._handle_missing_data(
            x_data, y_data, series.missing_data_method
        )

        # Apply smoothing
        if series.smoothing_enabled:
            y_data = self._smooth_data(y_data, series.smoothing_window)

        # Determine color
        color = series.color or self.color_cycle[index % len(self.color_cycle)]

        # Plot based on type
        plot_type = self.current_config.get('plot_type', PlotTypes.LINE.value)

        if plot_type == PlotTypes.LINE.value:
            self._plot_line(x_data, y_data, series, color)
        elif plot_type == PlotTypes.SCATTER.value:
            self._plot_scatter(x_data, y_data, series, color)
        elif plot_type == PlotTypes.BAR.value:
            self._plot_bar(x_data, y_data, series, color)
        elif plot_type == PlotTypes.AREA.value:
            self._plot_area(x_data, y_data, series, color)
        else:
            self._plot_line(x_data, y_data, series, color)

        # Add trend line
        if series.show_trendline:
            self._add_trendline(x_data, y_data, series, color)

        # Add statistics box
        if series.show_statistics:
            self._add_statistics_box(y_data, series)

        # Mark peaks
        if series.show_peaks:
            self._mark_peaks(x_data, y_data, series)

    def _plot_line(self, x_data, y_data, series: SeriesConfig, color: str):
        """Create line plot"""
        self.axes.plot(
            x_data, y_data,
            label=series.legend_label,
            color=color,
            linestyle=series.line_style,
            linewidth=series.line_width,
            marker=series.marker,
            markersize=series.marker_size,
            alpha=series.alpha
        )

    def _plot_scatter(self, x_data, y_data, series: SeriesConfig, color: str):
        """Create scatter plot"""
        self.axes.scatter(
            x_data, y_data,
            label=series.legend_label,
            color=color,
            s=series.marker_size ** 2,
            marker=series.marker or 'o',
            alpha=series.alpha
        )

    def _plot_bar(self, x_data, y_data, series: SeriesConfig, color: str):
        """Create bar plot"""
        # For multiple series, offset bars
        num_series = len([s for s in self.current_config.get('series', []) if s.visible])
        if num_series > 1:
            width = 0.8 / num_series
            offset = width * self.current_config.get('series_index', 0)
            x_positions = np.arange(len(x_data)) + offset
        else:
            x_positions = np.arange(len(x_data))
            width = 0.8

        self.axes.bar(
            x_positions, y_data,
            width=width,
            label=series.legend_label,
            color=color,
            alpha=series.alpha
        )

        # Set x-tick labels
        self.axes.set_xticks(np.arange(len(x_data)))
        self.axes.set_xticklabels(x_data, rotation=45, ha='right')

    def _plot_area(self, x_data, y_data, series: SeriesConfig, color: str):
        """Create area plot"""
        self.axes.fill_between(
            x_data, y_data, 0,
            label=series.legend_label,
            color=color,
            alpha=series.alpha * 0.5
        )
        self.axes.plot(
            x_data, y_data,
            color=color,
            linewidth=series.line_width,
            alpha=series.alpha
        )

    def _handle_missing_data(self, x_data, y_data, method: str):
        """Handle missing data in series"""

        # Create mask for valid data
        mask = ~(pd.isna(x_data) | pd.isna(y_data))

        if method == MissingDataMethods.DROP.value:
            return x_data[mask], y_data[mask]

        elif method == MissingDataMethods.INTERPOLATE.value:
            y_series = pd.Series(y_data)
            y_series = y_series.interpolate(method='linear')
            return x_data, y_series.values

        elif method == MissingDataMethods.FORWARD_FILL.value:
            y_series = pd.Series(y_data)
            y_series = y_series.fillna(method='ffill')
            return x_data, y_series.values

        elif method == MissingDataMethods.BACKWARD_FILL.value:
            y_series = pd.Series(y_data)
            y_series = y_series.fillna(method='bfill')
            return x_data, y_series.values

        elif method == MissingDataMethods.ZERO.value:
            y_data = np.nan_to_num(y_data, 0)
            return x_data, y_data

        elif method == MissingDataMethods.MEAN.value:
            mean_val = np.nanmean(y_data)
            y_data = np.nan_to_num(y_data, mean_val)
            return x_data, y_data

        return x_data[mask], y_data[mask]

    def _smooth_data(self, data, window: int):
        """Apply smoothing to data"""
        if len(data) < window:
            return data

        try:
            # Use Savitzky-Golay filter
            return savgol_filter(data, window, min(3, window - 1))
        except:
            # Fallback to moving average
            return pd.Series(data).rolling(window, center=True).mean().fillna(data).values

    def _add_trendline(self, x_data, y_data, series: SeriesConfig, color: str):
        """Add trend line to plot"""

        # Prepare data
        valid_mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_clean = x_data[valid_mask]
        y_clean = y_data[valid_mask]

        if len(x_clean) < 2:
            return

        # Convert datetime to numeric if needed
        if pd.api.types.is_datetime64_any_dtype(x_clean):
            x_numeric = mdates.date2num(x_clean)
        else:
            x_numeric = x_clean

        trend_type = series.trend_type

        if trend_type == TrendTypes.LINEAR.value:
            # Linear regression
            z = np.polyfit(x_numeric, y_clean, 1)
            p = np.poly1d(z)
            trend_y = p(x_numeric)

        elif trend_type == TrendTypes.POLYNOMIAL.value:
            # Polynomial regression
            z = np.polyfit(x_numeric, y_clean, series.trend_order)
            p = np.poly1d(z)
            trend_y = p(x_numeric)

        elif trend_type == TrendTypes.EXPONENTIAL.value:
            # Exponential fit (log-linear)
            y_log = np.log(np.abs(y_clean) + 1e-10)
            z = np.polyfit(x_numeric, y_log, 1)
            trend_y = np.exp(np.polyval(z, x_numeric))

        elif trend_type == TrendTypes.MOVING_AVERAGE.value:
            # Moving average
            window = min(len(y_clean) // 4, 20)
            trend_y = pd.Series(y_clean).rolling(window, center=True).mean().values

        else:
            return

        # Plot trend line
        self.axes.plot(
            x_clean, trend_y,
            '--',
            color=color,
            alpha=0.7,
            linewidth=2,
            label=f'{series.name} trend'
        )

    def _add_statistics_box(self, y_data, series: SeriesConfig):
        """Add statistics text box"""

        # Calculate statistics
        stats = StatisticalAnalyzer.calculate_basic_stats(y_data)

        # Create text
        text = f"{series.name}\\n"
        text += f"Mean: {stats['mean']:.3g}\\n"
        text += f"Std: {stats['std']:.3g}\\n"
        text += f"Min: {stats['min']:.3g}\\n"
        text += f"Max: {stats['max']:.3g}"

        # Add text box
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        self.axes.text(
            0.02, 0.98, text,
            transform=self.axes.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=props
        )

    def _mark_peaks(self, x_data, y_data, series: SeriesConfig):
        """Mark peaks and valleys"""
        from scipy.signal import find_peaks

        # Find peaks
        prominence = series.peak_prominence * (np.max(y_data) - np.min(y_data))
        peaks, _ = find_peaks(y_data, prominence=prominence)

        if len(peaks) > 0:
            self.axes.scatter(
                x_data[peaks], y_data[peaks],
                marker='^', s=100, color='red',
                zorder=5, label=f'{series.name} peaks'
            )

        # Find valleys (invert and find peaks)
        valleys, _ = find_peaks(-y_data, prominence=prominence)

        if len(valleys) > 0:
            self.axes.scatter(
                x_data[valleys], y_data[valleys],
                marker='v', s=100, color='blue',
                zorder=5, label=f'{series.name} valleys'
            )

    def _configure_axes(self, config: Dict[str, Any]):
        """Configure plot axes"""

        # Set labels
        self.axes.set_title(
            config.get('title', 'Data Analysis'),
            fontsize=config.get('title_size', PlotConfig.TITLE_SIZE),
            fontweight='bold',
            pad=20
        )

        self.axes.set_xlabel(
            config.get('xlabel', 'X Axis'),
            fontsize=config.get('xlabel_size', PlotConfig.LABEL_SIZE)
        )

        self.axes.set_ylabel(
            config.get('ylabel', 'Y Axis'),
            fontsize=config.get('ylabel_size', PlotConfig.LABEL_SIZE)
        )

        # Set scales
        if config.get('log_scale_x', False):
            self.axes.set_xscale('log')

        if config.get('log_scale_y', False):
            self.axes.set_yscale('log')

        # Set limits if specified
        if 'x_min' in config and 'x_max' in config:
            try:
                self.axes.set_xlim(float(config['x_min']), float(config['x_max']))
            except:
                pass

        if 'y_min' in config and 'y_max' in config:
            try:
                self.axes.set_ylim(float(config['y_min']), float(config['y_max']))
            except:
                pass

        # Format datetime axis if needed
        if detect_datetime_axis(self.axes.get_xlim()):
            self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            self.axes.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()

    def _add_grid(self, config: Dict[str, Any]):
        """Add grid to plot"""
        self.axes.grid(
            True,
            linestyle=config.get('grid_style', PlotConfig.GRID_STYLE),
            alpha=config.get('grid_alpha', PlotConfig.GRID_ALPHA),
            which='both'
        )
        self.axes.set_axisbelow(True)

    def _add_legend(self, config: Dict[str, Any]):
        """Add legend to plot"""
        handles, labels = self.axes.get_legend_handles_labels()

        if handles:
            self.axes.legend(
                handles, labels,
                loc=config.get('legend_location', 'best'),
                fontsize=config.get('legend_size', PlotConfig.LEGEND_SIZE),
                frameon=True,
                fancybox=True,
                shadow=True
            )

    def _apply_theme(self, theme: str):
        """Apply visual theme to plot"""
        if theme == 'dark':
            plt.style.use('dark_background')
        elif theme == 'seaborn':
            plt.style.use('seaborn-v0_8-whitegrid')
        elif theme == 'ggplot':
            plt.style.use('ggplot')
        else:
            plt.style.use('default')

    def export_plot(self, filepath: str, dpi: Optional[int] = None):
        """Export plot to file"""
        if not self.figure:
            raise ValueError("No plot to export")

        export_dpi = dpi or PlotConfig.EXPORT_DPI
        self.figure.savefig(
            filepath,
            dpi=export_dpi,
            bbox_inches='tight',
            facecolor=self.figure.get_facecolor()
        )

        logger.info(f"Plot exported to: {filepath}")

    def clear(self):
        """Clear current plot"""
        if self.axes:
            self.axes.clear()
        if self.figure:
            self.figure.clear()

        self.figure = None
        self.axes = None