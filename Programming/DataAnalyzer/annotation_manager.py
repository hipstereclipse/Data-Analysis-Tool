#!/usr/bin/env python3
"""
annotation_manager.py - Enhanced annotation management system for plots
Handles data-aware annotations with improved positioning and interaction
"""

import uuid
import json
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch, FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
import matplotlib.pyplot as plt


class AnnotationManager:
    """
    Enhanced annotation manager with data-aware positioning
    """

    def __init__(self):
        """Initialize annotation manager with enhanced features"""
        self.annotations = {}
        self.annotation_id_counter = 0
        self.selected_annotation = None

        # Store axis limits for data-aware positioning
        self.x_limits = None
        self.y_limits = None
        self.x_data_range = None
        self.y_data_range = None

        # Store reference to current axes
        self.current_ax = None

    def set_data_context(self, ax):
        """
        Set the data context from current axes

        Args:
            ax: Matplotlib axes object
        """
        self.current_ax = ax
        if ax:
            self.x_limits = ax.get_xlim()
            self.y_limits = ax.get_ylim()
            self.x_data_range = self.x_limits[1] - self.x_limits[0]
            self.y_data_range = self.y_limits[1] - self.y_limits[0]

    def convert_relative_to_data(self, rel_x, rel_y):
        """
        Convert relative coordinates (0-1) to data coordinates

        Args:
            rel_x: Relative X position (0-1)
            rel_y: Relative Y position (0-1)

        Returns:
            tuple: (data_x, data_y)
        """
        if self.x_limits and self.y_limits:
            data_x = self.x_limits[0] + rel_x * self.x_data_range
            data_y = self.y_limits[0] + rel_y * self.y_data_range
            return data_x, data_y
        return rel_x, rel_y

    def convert_data_to_relative(self, data_x, data_y):
        """
        Convert data coordinates to relative coordinates (0-1)

        Args:
            data_x: Data X position
            data_y: Data Y position

        Returns:
            tuple: (rel_x, rel_y)
        """
        if self.x_limits and self.y_limits and self.x_data_range and self.y_data_range:
            rel_x = (data_x - self.x_limits[0]) / self.x_data_range
            rel_y = (data_y - self.y_limits[0]) / self.y_data_range
            return rel_x, rel_y
        return data_x, data_y

    def add_data_annotation(self, ann_type, **kwargs):
        """
        Add annotation with data-aware positioning

        Args:
            ann_type: Type of annotation
            **kwargs: Annotation parameters including data coordinates

        Returns:
            str: Annotation ID
        """
        self.annotation_id_counter += 1
        ann_id = f"ann_{self.annotation_id_counter}"

        # Create annotation with data coordinates
        annotation = {
            'id': ann_id,
            'type': ann_type,
            'visible': kwargs.get('visible', True),
            'editable': kwargs.get('editable', True),
            'use_data_coords': kwargs.get('use_data_coords', True),
            **kwargs
        }

        self.annotations[ann_id] = annotation
        return ann_id

    def add_spike_annotation(self, x_start, x_end, y_max, label="Spike", color='red'):
        """
        Add spike annotation with shaded region and marker

        Args:
            x_start: Start X position in data coordinates
            x_end: End X position in data coordinates
            y_max: Maximum Y value of spike
            label: Annotation label
            color: Highlight color

        Returns:
            str: Annotation ID
        """
        return self.add_data_annotation(
            'spike_region',
            x_start=x_start,
            x_end=x_end,
            y_max=y_max,
            label=label,
            color=color,
            alpha=0.3,
            marker_color='red',
            marker_size=100
        )

    def add_leak_annotation(self, x_start, x_end, slope, label="Leak", color='orange'):
        """
        Add leak rate annotation with trend line

        Args:
            x_start: Start X position
            x_end: End X position
            slope: Leak rate slope
            label: Annotation label
            color: Highlight color

        Returns:
            str: Annotation ID
        """
        return self.add_data_annotation(
            'leak_region',
            x_start=x_start,
            x_end=x_end,
            slope=slope,
            label=label,
            color=color,
            alpha=0.2,
            show_trend=True
        )

    def add_pumpdown_annotation(self, x_start, x_end, p_initial, p_final, time_to_base, label="Pump-down"):
        """
        Add pump-down annotation with info box

        Args:
            x_start: Start X position
            x_end: End X position
            p_initial: Initial pressure
            p_final: Final pressure
            time_to_base: Time to reach base pressure
            label: Annotation label

        Returns:
            str: Annotation ID
        """
        return self.add_data_annotation(
            'pumpdown_region',
            x_start=x_start,
            x_end=x_end,
            p_initial=p_initial,
            p_final=p_final,
            time_to_base=time_to_base,
            label=label,
            color='green',
            alpha=0.2,
            show_info_box=True
        )

    def add_data_point_annotation(self, x_data, y_data, label, **kwargs):
        """
        Add annotation at specific data point

        Args:
            x_data: X data coordinate
            y_data: Y data coordinate
            label: Annotation text
            **kwargs: Additional styling parameters

        Returns:
            str: Annotation ID
        """
        return self.add_data_annotation(
            'data_point',
            x_pos=x_data,
            y_pos=y_data,
            label=label,
            text=label,
            marker=kwargs.get('marker', 'o'),
            color=kwargs.get('color', 'red'),
            size=kwargs.get('size', 100),
            show_arrow=kwargs.get('show_arrow', True),
            arrow_props=kwargs.get('arrow_props', dict(arrowstyle='->', lw=2))
        )

    def add_data_arrow(self, x1_data, y1_data, x2_data, y2_data, label="", **kwargs):
        """
        Add arrow between two data points

        Args:
            x1_data, y1_data: Start point in data coordinates
            x2_data, y2_data: End point in data coordinates
            label: Optional label
            **kwargs: Arrow styling

        Returns:
            str: Annotation ID
        """
        return self.add_data_annotation(
            'data_arrow',
            x_start=x1_data,
            y_start=y1_data,
            x_end=x2_data,
            y_end=y2_data,
            label=label,
            color=kwargs.get('color', 'black'),
            style=kwargs.get('style', '->'),
            width=kwargs.get('width', 2),
            connection_style=kwargs.get('connection_style', 'arc3,rad=0.1')
        )

    def draw_annotations(self, ax, picker=True):
        """
        Draw all visible annotations on axes with enhanced rendering

        Args:
            ax: Matplotlib axes
            picker: Enable picking for interaction

        Returns:
            dict: Artist to annotation ID mapping
        """
        artists = {}
        self.set_data_context(ax)

        for ann_id, ann in self.annotations.items():
            if not ann.get('visible', True):
                continue

            artist = None
            ann_type = ann['type']

            # Handle different annotation types
            if ann_type == 'spike_region':
                # Draw spike region with marker
                artist = self._draw_spike_region(ax, ann, picker)

            elif ann_type == 'leak_region':
                # Draw leak region with trend
                artist = self._draw_leak_region(ax, ann, picker)

            elif ann_type == 'pumpdown_region':
                # Draw pump-down region with info
                artist = self._draw_pumpdown_region(ax, ann, picker)

            elif ann_type == 'data_point':
                # Draw point with label
                artist = self._draw_data_point(ax, ann, picker)

            elif ann_type == 'data_arrow':
                # Draw arrow between data points
                artist = self._draw_data_arrow(ax, ann, picker)

            elif ann_type == 'vline':
                # Vertical line at data X position
                artist = ax.axvline(
                    x=ann['x_pos'],
                    color=ann.get('color', 'red'),
                    linestyle=ann.get('style', '--'),
                    linewidth=ann.get('width', 2),
                    alpha=ann.get('alpha', 0.8),
                    label=ann.get('label'),
                    picker=picker
                )

            elif ann_type == 'hline':
                # Horizontal line at data Y position
                artist = ax.axhline(
                    y=ann['y_pos'],
                    color=ann.get('color', 'blue'),
                    linestyle=ann.get('style', '--'),
                    linewidth=ann.get('width', 2),
                    alpha=ann.get('alpha', 0.8),
                    label=ann.get('label'),
                    picker=picker
                )

            elif ann_type == 'region':
                # Shaded region
                artist = ax.axvspan(
                    ann['x_start'],
                    ann['x_end'],
                    color=ann.get('color', 'yellow'),
                    alpha=ann.get('alpha', 0.3),
                    label=ann.get('label'),
                    picker=picker
                )

            if artist:
                artists[artist] = ann_id

        return artists

    def _draw_spike_region(self, ax, ann, picker):
        """Draw spike region with enhanced visualization"""
        # Draw shaded region
        region = ax.axvspan(
            ann['x_start'],
            ann['x_end'],
            color=ann.get('color', 'red'),
            alpha=ann.get('alpha', 0.3),
            label=ann.get('label')
        )

        # Add peak marker if y_max provided
        if 'y_max' in ann:
            x_center = (ann['x_start'] + ann['x_end']) / 2
            ax.scatter(
                x_center,
                ann['y_max'],
                marker='^',
                s=ann.get('marker_size', 100),
                color=ann.get('marker_color', 'red'),
                zorder=10,
                edgecolors='black',
                linewidths=2
            )

            # Add label at peak
            if ann.get('label'):
                ax.annotate(
                    ann['label'],
                    xy=(x_center, ann['y_max']),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2')
                )

        return region

    def _draw_leak_region(self, ax, ann, picker):
        """Draw leak region with trend line"""
        # Draw shaded region
        region = ax.axvspan(
            ann['x_start'],
            ann['x_end'],
            color=ann.get('color', 'orange'),
            alpha=ann.get('alpha', 0.2),
            label=ann.get('label')
        )

        # Add trend line if requested
        if ann.get('show_trend') and 'slope' in ann:
            x_points = np.array([ann['x_start'], ann['x_end']])
            # Need to get actual y values from data or estimate
            if self.y_limits:
                y_center = (self.y_limits[0] + self.y_limits[1]) / 2
                y_points = y_center + ann['slope'] * (x_points - x_points[0])
                ax.plot(x_points, y_points, 'r--', linewidth=2, alpha=0.7)

        # Add label
        if ann.get('label'):
            x_center = (ann['x_start'] + ann['x_end']) / 2
            if self.y_limits:
                y_pos = self.y_limits[1] - 0.1 * self.y_data_range
                ax.text(
                    x_center,
                    y_pos,
                    ann['label'],
                    fontsize=10,
                    ha='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.5)
                )

        return region

    def _draw_pumpdown_region(self, ax, ann, picker):
        """Draw pump-down region with info box"""
        # Draw shaded region
        region = ax.axvspan(
            ann['x_start'],
            ann['x_end'],
            color=ann.get('color', 'green'),
            alpha=ann.get('alpha', 0.2),
            label=ann.get('label')
        )

        # Add info box if requested
        if ann.get('show_info_box'):
            info_text = f"{ann.get('label', 'Pump-down')}\n"
            if 'p_initial' in ann:
                info_text += f"P₀: {ann['p_initial']:.2e} mbar\n"
            if 'p_final' in ann:
                info_text += f"P_f: {ann['p_final']:.2e} mbar\n"
            if 'time_to_base' in ann:
                info_text += f"Time: {ann['time_to_base']:.1f} min"

            x_center = (ann['x_start'] + ann['x_end']) / 2
            if self.y_limits:
                y_pos = self.y_limits[0] + 0.8 * self.y_data_range
                ax.text(
                    x_center,
                    y_pos,
                    info_text,
                    fontsize=9,
                    ha='center',
                    va='top',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8)
                )

        return region

    def _draw_data_point(self, ax, ann, picker):
        """Draw annotated data point"""
        # Draw marker
        scatter = ax.scatter(
            ann['x_pos'],
            ann['y_pos'],
            marker=ann.get('marker', 'o'),
            s=ann.get('size', 100),
            color=ann.get('color', 'red'),
            zorder=10,
            picker=picker,
            edgecolors='black' if ann['id'] == self.selected_annotation else 'none',
            linewidths=2 if ann['id'] == self.selected_annotation else 0
        )

        # Add label with arrow
        if ann.get('text') and ann.get('show_arrow', True):
            ax.annotate(
                ann['text'],
                xy=(ann['x_pos'], ann['y_pos']),
                xytext=(20, 20),
                textcoords='offset points',
                fontsize=ann.get('fontsize', 10),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                arrowprops=ann.get('arrow_props', dict(arrowstyle='->', lw=1.5))
            )

        return scatter

    def _draw_data_arrow(self, ax, ann, picker):
        """Draw arrow between data points"""
        arrow = FancyArrowPatch(
            (ann['x_start'], ann['y_start']),
            (ann['x_end'], ann['y_end']),
            arrowstyle=ann.get('style', '->'),
            color=ann.get('color', 'black'),
            linewidth=ann.get('width', 2),
            connectionstyle=ann.get('connection_style', 'arc3,rad=0.1'),
            mutation_scale=20,
            alpha=ann.get('alpha', 0.8)
        )
        ax.add_patch(arrow)

        # Add label at midpoint if provided
        if ann.get('label'):
            x_mid = (ann['x_start'] + ann['x_end']) / 2
            y_mid = (ann['y_start'] + ann['y_end']) / 2
            ax.text(
                x_mid,
                y_mid,
                ann['label'],
                fontsize=10,
                ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)
            )

        return arrow

    def find_annotations_in_range(self, x_start, x_end):
        """
        Find annotations within X data range

        Args:
            x_start: Start X position
            x_end: End X position

        Returns:
            list: Annotation IDs in range
        """
        found = []

        for ann_id, ann in self.annotations.items():
            if ann['type'] in ['spike_region', 'leak_region', 'pumpdown_region', 'region']:
                if ann['x_start'] <= x_end and ann['x_end'] >= x_start:
                    found.append(ann_id)
            elif ann['type'] == 'vline':
                if x_start <= ann['x_pos'] <= x_end:
                    found.append(ann_id)
            elif ann['type'] in ['data_point', 'point']:
                if 'x_pos' in ann and x_start <= ann['x_pos'] <= x_end:
                    found.append(ann_id)

        return found