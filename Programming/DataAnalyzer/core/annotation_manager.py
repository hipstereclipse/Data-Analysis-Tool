#!/usr/bin/env python3
"""
core/annotation_manager.py - Annotation Manager
Handles plot annotations including text, arrows, and shapes
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
from typing import List, Dict, Optional, Any, Tuple
import logging
import uuid

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
        
        # Real-time preview support
        self.preview_annotation = None
        self.preview_object = None
        self.preview_mode = False
        
        # Drag/move support
        self.dragging_annotation = None
        self.drag_start_pos = None
        self.drag_event_ids = []

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

    def refresh_plot_annotations(self):
        """Clear drawn artists and redraw all annotations on the current axes.

        Safe to call anytime; no-ops if axes is not set.
        """
        if not self.current_axes:
            return
        try:
            # Remove existing artists from axes
            for ann_id, obj in list(self.annotation_objects.items()):
                try:
                    if hasattr(obj, 'remove'):
                        obj.remove()
                except Exception:
                    pass
                finally:
                    self.annotation_objects.pop(ann_id, None)

            # Redraw all visible annotations
            self.draw_all_annotations(self.current_axes)

            # Request a canvas refresh if available
            fig = self.current_axes.figure if hasattr(self.current_axes, 'figure') else None
            if fig and hasattr(fig.canvas, 'draw_idle'):
                fig.canvas.draw_idle()
        except Exception as e:
            logger.error(f"Failed refreshing plot annotations: {e}")

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

            # Normalize potential datetime x-coordinates to Matplotlib float dates
            def _norm_x(val):
                try:
                    # If it's already a float/int, return as-is
                    if isinstance(val, (int, float)):
                        return float(val)
                    # pandas/np datetime64 or python datetime
                    return mdates.date2num(val)
                except Exception:
                    try:
                        # Try to parse common string dates
                        import pandas as pd
                        return mdates.date2num(pd.to_datetime(val, errors='coerce'))
                    except Exception:
                        # Fallback: best-effort float cast
                        try:
                            return float(val)
                        except Exception:
                            return val

            x = _norm_x(annotation.x)
            x2 = _norm_x(annotation.x2)

            if annotation.annotation_type == "text":
                ann_obj = ax.annotate(
                    annotation.text,
                    xy=(x, annotation.y),
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
                    xy=(x2, annotation.y2),
                    xytext=(x, annotation.y),
                    xycoords='data' if self.is_data_coordinates(annotation) else 'axes fraction',
                    textcoords='data' if self.is_data_coordinates(annotation) else 'axes fraction',
                    arrowprops=dict(
                        arrowstyle=annotation.arrow_style or "->",
                        color=annotation.color,
                        lw=annotation.arrow_width,
                        mutation_scale=getattr(annotation, 'arrow_mutation_scale', 12.0),
                        alpha=annotation.alpha
                    ),
                    fontsize=annotation.font_size if annotation.text else 0,
                    color=annotation.color
                )

            elif annotation.annotation_type == "line":
                x_vals = [x, x2]
                y_vals = [annotation.y, annotation.y2]
                ann_obj = ax.plot(
                    x_vals, y_vals,
                    color=annotation.color,
                    linewidth=annotation.border_width,
                    linestyle=annotation.line_style if hasattr(annotation, 'line_style') else '-',
                    alpha=annotation.alpha
                )[0]

            elif annotation.annotation_type == "point":
                ann_obj = ax.scatter(
                    [x], [annotation.y],
                    color=annotation.color,
                    s=(annotation.marker_size or 6.0) ** 2 / 2.0,
                    marker=getattr(annotation, 'marker', 'o') or 'o',
                    alpha=annotation.alpha,
                    zorder=3
                )
                # Optional text label near the point
                if annotation.text:
                    ax.annotate(
                        annotation.text,
                        xy=(x, annotation.y),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=max(8, int(annotation.font_size or 10)),
                        color=annotation.color,
                        alpha=annotation.alpha
                    )

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
                           series_name: str = "", label: str = "", color: str = "red") -> AnnotationConfig:
        """
        Add spike annotation for vacuum analysis
        
        Args:
            x: X coordinate (start of spike)
            y: Y coordinate (could be end of spike)  
            magnitude: Spike magnitude
            series_name: Name of the series
            label: Label for the spike annotation
            color: Color for the annotation
            
        Returns:
            Created AnnotationConfig
        """
        # Use provided label or create default
        annotation_text = label if label else f"Spike: {magnitude:.2e} ({series_name})"
        
        annotation = AnnotationConfig(
            annotation_type="point",
            text=annotation_text,
            x=x,
            y=y,
            color=color,
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

    # ---- General-purpose helpers for common primitives ----
    def add_text(self, text: str, x: float, y: float, color: str = "#000000",
                 font_size: float = 12.0, background_color: Optional[str] = None,
                 border_color: Optional[str] = None, alpha: float = 1.0) -> AnnotationConfig:
        """Add a text label at data coordinates."""
        ann = AnnotationConfig(
            annotation_type="text",
            text=text,
            x=x,
            y=y,
            color=color,
            font_size=font_size,
            background_color=background_color,
            border_color=border_color,
            alpha=alpha,
        )
        self.add_annotation(ann)
        return ann

    def add_line(self, x1: float, y1: float, x2: float, y2: float,
                 color: str = "#000000", line_style: str = "-",
                 width: float = 1.5, alpha: float = 1.0) -> AnnotationConfig:
        """Add a simple line segment between two points."""
        ann = AnnotationConfig(
            annotation_type="line",
            x=x1,
            y=y1,
            x2=x2,
            y2=y2,
            color=color,
            line_style=line_style,
            border_width=width,
            alpha=alpha,
        )
        self.add_annotation(ann)
        return ann

    def add_arrow(self, x_from: float, y_from: float, x_to: float, y_to: float,
                   text: str = "", color: str = "#000000", width: float = 1.5,
                   style: str = "->", alpha: float = 1.0) -> AnnotationConfig:
        """Add an arrow from (x_from, y_from) to (x_to, y_to) with optional text."""
        ann = AnnotationConfig(
            annotation_type="arrow",
            text=text,
            x=x_from,
            y=y_from,
            x2=x_to,
            y2=y_to,
            color=color,
            arrow_style=style,
            arrow_width=width,
            alpha=alpha,
        )
        self.add_annotation(ann)
        return ann

    def add_point(self, x: float, y: float, text: str = "", color: str = "#000000",
                   marker: str = "o", marker_size: float = 6.0, alpha: float = 1.0) -> AnnotationConfig:
        """Add a labeled point/marker annotation."""
        ann = AnnotationConfig(
            annotation_type="point",
            text=text,
            x=x,
            y=y,
            color=color,
            marker=marker,
            marker_size=marker_size,
            alpha=alpha,
        )
        self.add_annotation(ann)
        return ann

    def add_rectangle(self, x: float, y: float, width: float, height: float,
                       color: str = "#000000", fill: bool = False, alpha: float = 1.0,
                       border_color: Optional[str] = None, border_width: float = 1.0) -> AnnotationConfig:
        """Add a rectangle patch given lower-left (x,y), width, height."""
        ann = AnnotationConfig(
            annotation_type="rect",
            x=x,
            y=y,
            width=width,
            height=height,
            color=color,
            fill=fill,
            alpha=alpha,
            border_color=border_color,
            border_width=border_width,
        )
        self.add_annotation(ann)
        return ann

    def add_circle(self, x: float, y: float, radius: float,
                    color: str = "#000000", fill: bool = False, alpha: float = 1.0,
                    border_color: Optional[str] = None, border_width: float = 1.0) -> AnnotationConfig:
        """Add a circle patch centered at (x,y) with given radius."""
        ann = AnnotationConfig(
            annotation_type="circle",
            x=x,
            y=y,
            radius=radius,
            color=color,
            fill=fill,
            alpha=alpha,
            border_color=border_color,
            border_width=border_width,
        )
        self.add_annotation(ann)
        return ann

    # ---- Real-time preview functionality ----
    def start_preview_mode(self):
        """Enable real-time preview mode"""
        self.preview_mode = True
        self._enable_drag_interactions()
    
    def stop_preview_mode(self):
        """Disable real-time preview mode"""
        self.preview_mode = False
        self.clear_preview()
        self._disable_drag_interactions()
    
    def update_preview(self, annotation_config: AnnotationConfig):
        """Update the preview annotation in real-time"""
        if not self.preview_mode or not self.current_axes:
            return
            
        # Clear existing preview
        self.clear_preview()
        
        # Store preview config
        self.preview_annotation = annotation_config
        
        # Draw preview (with slightly different styling)
        preview_config = AnnotationConfig(**annotation_config.to_dict())
        preview_config.alpha = min(0.7, preview_config.alpha)  # Make preview semi-transparent
        preview_config.annotation_id = "preview"
        
        # Draw the preview
        self.draw_annotation(preview_config)
        self.preview_object = self.annotation_objects.get("preview")
        
        # Refresh canvas
        if self.current_axes and hasattr(self.current_axes, 'figure'):
            self.current_axes.figure.canvas.draw_idle()
    
    def clear_preview(self):
        """Clear the current preview annotation"""
        if self.preview_object and hasattr(self.preview_object, 'remove'):
            try:
                self.preview_object.remove()
            except:
                pass
        self.preview_object = None
        self.preview_annotation = None
        if "preview" in self.annotation_objects:
            del self.annotation_objects["preview"]
        
        # Refresh canvas
        if self.current_axes and hasattr(self.current_axes, 'figure'):
            self.current_axes.figure.canvas.draw_idle()
    
    def commit_preview(self):
        """Convert the current preview to a permanent annotation"""
        if self.preview_annotation:
            # Create permanent annotation
            permanent_config = AnnotationConfig(**self.preview_annotation.to_dict())
            permanent_config.alpha = self.preview_annotation.alpha  # Restore original alpha
            permanent_config.annotation_id = str(uuid.uuid4())  # New ID
            
            # Clear preview first
            self.clear_preview()
            
            # Add as permanent annotation
            self.add_annotation(permanent_config)
            return permanent_config
        return None
    
    # ---- Drag/move/resize functionality ----
    def _enable_drag_interactions(self):
        """Enable drag/move/resize interactions"""
        if not self.current_axes:
            return
            
        canvas = self.current_axes.figure.canvas
        
        # Connect event handlers
        self.drag_event_ids = [
            canvas.mpl_connect('button_press_event', self._on_mouse_press),
            canvas.mpl_connect('button_release_event', self._on_mouse_release),
            canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        ]
    
    def _disable_drag_interactions(self):
        """Disable drag/move/resize interactions"""
        if not self.current_axes:
            return
            
        canvas = self.current_axes.figure.canvas
        
        # Disconnect event handlers
        for event_id in self.drag_event_ids:
            try:
                canvas.mpl_disconnect(event_id)
            except:
                pass
        self.drag_event_ids.clear()
    
    def _on_mouse_press(self, event):
        """Handle mouse press for drag interactions"""
        if not event.inaxes == self.current_axes:
            return
            
        # Find annotation under cursor
        annotation = self._find_annotation_at_point(event.xdata, event.ydata)
        if annotation:
            self.dragging_annotation = annotation
            self.drag_start_pos = (event.xdata, event.ydata)
            return True
        return False
    
    def _on_mouse_release(self, event):
        """Handle mouse release for drag interactions"""
        if self.dragging_annotation:
            self.dragging_annotation = None
            self.drag_start_pos = None
            # Refresh plot after drag
            self.refresh_plot_annotations()
    
    def _on_mouse_motion(self, event):
        """Handle mouse motion for drag interactions"""
        if not self.dragging_annotation or not self.drag_start_pos:
            return
            
        if not event.inaxes == self.current_axes:
            return
            
        # Calculate drag delta
        dx = event.xdata - self.drag_start_pos[0]
        dy = event.ydata - self.drag_start_pos[1]
        
        # Update annotation position
        self.dragging_annotation.x += dx
        self.dragging_annotation.y += dy
        
        # Update secondary coordinates for lines/arrows
        if hasattr(self.dragging_annotation, 'x2'):
            self.dragging_annotation.x2 += dx
        if hasattr(self.dragging_annotation, 'y2'):
            self.dragging_annotation.y2 += dy
            
        # Update drag start position
        self.drag_start_pos = (event.xdata, event.ydata)
        
        # Redraw annotation
        self.update_annotation(self.dragging_annotation)
    
    def _find_annotation_at_point(self, x: float, y: float, tolerance: float = 0.05) -> Optional[AnnotationConfig]:
        """Find annotation near the given point"""
        if not self.current_axes:
            return None
            
        # Get axis limits for tolerance calculation
        x_range = self.current_axes.get_xlim()[1] - self.current_axes.get_xlim()[0]
        y_range = self.current_axes.get_ylim()[1] - self.current_axes.get_ylim()[0]
        x_tol = x_range * tolerance
        y_tol = y_range * tolerance
        
        for annotation in self.annotations:
            if not annotation.visible:
                continue
                
            # Check if point is near annotation
            if (abs(annotation.x - x) <= x_tol and 
                abs(annotation.y - y) <= y_tol):
                return annotation
        
        return None