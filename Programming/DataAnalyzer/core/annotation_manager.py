#!/usr/bin/env python3
"""
core/annotation_manager.py - Annotation Manager
Handles plot annotations including text, arrows, and shapes
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Optional, Any, Tuple
import logging

from models.data_models import AnnotationConfig

logger = logging.getLogger(__name__)


class AnnotationManager:
    """
    Manages plot annotations
    Handles adding, removing, and updating annotations on plots
    """

    def __init__(self):
        """Initialize annotation manager"""
        self.annotations: List[AnnotationConfig] = []
        self.annotation_objects: Dict[str, Any] = {}
        self.current_axes = None
        self.data_context = None

    def set_data_context(self, axes):
        """
        Set the current axes and data context

        Args:
            axes: Matplotlib axes object
        """
        self.current_axes = axes
        if axes:
            self.data_context = {
                'xlim': axes.get_xlim(),
                'ylim': axes.get_ylim(),
                'xscale': axes.get_xscale(),
                'yscale': axes.get_yscale()
            }

    def add_annotation(self, annotation: AnnotationConfig):
        """
        Add an annotation

        Args:
            annotation: AnnotationConfig object
        """
        self.annotations.append(annotation)
        if self.current_axes:
            self.draw_annotation(annotation)

    def remove_annotation(self, annotation_id: str):
        """
        Remove an annotation

        Args:
            annotation_id: Annotation identifier
        """
        # Remove from list
        self.annotations = [a for a in self.annotations if a.annotation_id != annotation_id]

        # Remove from plot
        if annotation_id in self.annotation_objects:
            obj = self.annotation_objects[annotation_id]
            if hasattr(obj, 'remove'):
                obj.remove()
            del self.annotation_objects[annotation_id]

    def clear_annotations(self):
        """Clear all annotations"""
        for ann_id in list(self.annotation_objects.keys()):
            self.remove_annotation(ann_id)
        self.annotations.clear()

    def draw_annotation(self, annotation: AnnotationConfig):
        """
        Draw a single annotation on the current axes

        Args:
            annotation: AnnotationConfig object
        """
        if not self.current_axes or not annotation.visible:
            return

        try:
            ax = self.current_axes
            ann_obj = None

            if annotation.annotation_type == "text":
                ann_obj = ax.annotate(
                    annotation.text,
                    xy=(annotation.x, annotation.y),
                    xycoords='data' if self.is_data_coordinates(annotation) else 'axes fraction',
                    fontsize=annotation.font_size,
                    fontfamily=annotation.font_family,
                    fontweight=annotation.font_weight,
                    fontstyle=annotation.font_style,
                    color=annotation.color,
                    ha=annotation.horizontal_alignment,
                    va=annotation.vertical_alignment,
                    rotation=annotation.rotation,
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor=annotation.background_color or 'white',
                              edgecolor=annotation.border_color or annotation.color,
                              linewidth=annotation.border_width,
                              alpha=annotation.alpha) if annotation.background_color else None
                )

            elif annotation.annotation_type == "arrow":
                ann_obj = ax.annotate(
                    annotation.text if annotation.text else "",
                    xy=(annotation.x2, annotation.y2),
                    xytext=(annotation.x, annotation.y),
                    xycoords='data' if self.is_data_coordinates(annotation) else 'axes fraction',
                    textcoords='data' if self.is_data_coordinates(annotation) else 'axes fraction',
                    arrowprops=dict(
                        arrowstyle=annotation.arrow_style or "->",
                        color=annotation.color,
                        lw=annotation.arrow_width,
                        alpha=annotation.alpha
                    ),
                    fontsize=annotation.font_size if annotation.text else 0,
                    color=annotation.color
                )

            elif annotation.annotation_type == "line":
                x_vals = [annotation.x, annotation.x2]
                y_vals = [annotation.y, annotation.y2]
                ann_obj = ax.plot(
                    x_vals, y_vals,
                    color=annotation.color,
                    linewidth=annotation.border_width,
                    linestyle=annotation.line_style if hasattr(annotation, 'line_style') else '-',
                    alpha=annotation.alpha
                )[0]

            elif annotation.annotation_type == "rect":
                # Convert coordinates if needed
                if self.is_data_coordinates(annotation):
                    xy = (annotation.x, annotation.y)
                    width = annotation.width
                    height = annotation.height
                else:
                    # For axes fraction coordinates
                    xy = ax.transAxes.transform((annotation.x, annotation.y))
                    xy = ax.transData.inverted().transform(xy)
                    width_point = ax.transAxes.transform((annotation.width, 0))[0]
                    height_point = ax.transAxes.transform((0, annotation.height))[1]
                    width = ax.transData.inverted().transform((width_point, 0))[0] - xy[0]
                    height = ax.transData.inverted().transform((0, height_point))[1] - xy[1]

                rect = patches.Rectangle(
                    xy, width, height,
                    linewidth=annotation.border_width,
                    edgecolor=annotation.border_color or annotation.color,
                    facecolor=annotation.color if annotation.fill else 'none',
                    alpha=annotation.alpha
                )
                ax.add_patch(rect)
                ann_obj = rect

            elif annotation.annotation_type == "circle":
                circle = patches.Circle(
                    (annotation.x, annotation.y),
                    annotation.radius,
                    linewidth=annotation.border_width,
                    edgecolor=annotation.border_color or annotation.color,
                    facecolor=annotation.color if annotation.fill else 'none',
                    alpha=annotation.alpha
                )
                ax.add_patch(circle)
                ann_obj = circle

            # Store reference
            if ann_obj:
                self.annotation_objects[annotation.annotation_id] = ann_obj

        except Exception as e:
            logger.error(f"Failed to draw annotation: {e}")

    def is_data_coordinates(self, annotation: AnnotationConfig) -> bool:
        """
        Determine if annotation uses data coordinates or axes fraction

        Args:
            annotation: AnnotationConfig object

        Returns:
            True if data coordinates, False if axes fraction
        """
        # Check if coordinates are likely to be data coordinates
        # This is a heuristic - could be improved with explicit flag
        if annotation.x > 1 or annotation.x < 0 or annotation.y > 1 or annotation.y < 0:
            return True
        return False

    def draw_annotations(self, axes):
        """
        Draw all annotations on given axes (alias for draw_all_annotations)

        Args:
            axes: Matplotlib axes object
        """
        self.draw_all_annotations(axes)

    def draw_all_annotations(self, axes):
        """
        Draw all annotations on given axes

        Args:
            axes: Matplotlib axes object
        """
        self.set_data_context(axes)
        for annotation in self.annotations:
            if annotation.visible:
                self.draw_annotation(annotation)

    def update_annotation(self, annotation: AnnotationConfig):
        """
        Update an existing annotation

        Args:
            annotation: Updated AnnotationConfig object
        """
        # Remove old annotation object
        if annotation.annotation_id in self.annotation_objects:
            obj = self.annotation_objects[annotation.annotation_id]
            if hasattr(obj, 'remove'):
                obj.remove()
            del self.annotation_objects[annotation.annotation_id]

        # Update in list
        for i, ann in enumerate(self.annotations):
            if ann.annotation_id == annotation.annotation_id:
                self.annotations[i] = annotation
                break

        # Redraw
        if self.current_axes:
            self.draw_annotation(annotation)

    def get_annotations(self) -> List[AnnotationConfig]:
        """Get all annotations"""
        return self.annotations

    def set_annotations(self, annotations: List[AnnotationConfig]):
        """Set annotations from list"""
        self.clear_annotations()
        self.annotations = annotations
        if self.current_axes:
            self.draw_all_annotations(self.current_axes)

    def find_annotation_at_point(self, x: float, y: float) -> Optional[AnnotationConfig]:
        """
        Find annotation at given point

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            AnnotationConfig if found, None otherwise
        """
        # Simple proximity check - could be improved
        for annotation in self.annotations:
            if annotation.annotation_type == "text":
                if abs(annotation.x - x) < 0.05 and abs(annotation.y - y) < 0.05:
                    return annotation
        return None

    def add_pumpdown_annotation(self, x_start: float, x_end: float, p_initial: float, 
                               p_final: float = None, time_to_base: float = None, 
                               label: str = "", series_name: str = "") -> AnnotationConfig:
        """
        Add pumpdown annotation for vacuum analysis
        
        Args:
            x_start: Start X coordinate
            x_end: End X coordinate  
            p_initial: Initial pressure
            p_final: Final pressure (optional)
            time_to_base: Time to base pressure (optional)
            label: Annotation label
            series_name: Name of the series
            
        Returns:
            Created AnnotationConfig
        """
        # Use label if provided, otherwise create default
        text = label if label else f"Pumpdown: {series_name}"
        
        annotation = AnnotationConfig(
            annotation_type="line",
            text=text,
            x=x_start,
            y=p_initial,
            x2=x_end,
            y2=p_final if p_final is not None else p_initial,
            color="#FF6B35",
            line_style="--",
            alpha=0.8
        )
        self.add_annotation(annotation)
        return annotation

    def add_spike_annotation(self, x: float, y: float, magnitude: float,
                           series_name: str = "") -> AnnotationConfig:
        """
        Add spike annotation for vacuum analysis
        
        Args:
            x: X coordinate
            y: Y coordinate
            magnitude: Spike magnitude
            series_name: Name of the series
            
        Returns:
            Created AnnotationConfig
        """
        annotation = AnnotationConfig(
            annotation_type="point",
            text=f"Spike: {magnitude:.2e} ({series_name})",
            x=x,
            y=y,
            color="#FF0000",
            marker="^",
            marker_size=8.0,
            alpha=0.9
        )
        self.add_annotation(annotation)
        return annotation

    def add_base_pressure_annotation(self, x_start: float, x_end: float, pressure: float,
                                   series_name: str = "") -> AnnotationConfig:
        """
        Add base pressure annotation for vacuum analysis
        
        Args:
            x_start: Start X coordinate
            x_end: End X coordinate
            pressure: Base pressure value
            series_name: Name of the series
            
        Returns:
            Created AnnotationConfig
        """
        annotation = AnnotationConfig(
            annotation_type="line",
            text=f"Base Pressure: {pressure:.2e} ({series_name})",
            x=x_start,
            y=pressure,
            x2=x_end,
            y2=pressure,
            color="#00AA00",
            line_style="-",
            alpha=0.7
        )
        self.add_annotation(annotation)
        return annotation

    def add_leak_annotation(self, x_start: float, x_end: float, leak_rate: float,
                          series_name: str = "") -> AnnotationConfig:
        """
        Add leak rate annotation for vacuum analysis
        
        Args:
            x_start: Start X coordinate
            x_end: End X coordinate
            leak_rate: Leak rate value
            series_name: Name of the series
            
        Returns:
            Created AnnotationConfig
        """
        # Calculate slope line
        y_start = 1e-8  # Base pressure assumption
        y_end = y_start + (leak_rate * (x_end - x_start))
        
        annotation = AnnotationConfig(
            annotation_type="line",
            text=f"Leak Rate: {leak_rate:.2e} mbar·l/s ({series_name})",
            x=x_start,
            y=y_start,
            x2=x_end,
            y2=y_end,
            color="#FFA500",
            line_style=":",
            alpha=0.8
        )
        self.add_annotation(annotation)
        return annotation