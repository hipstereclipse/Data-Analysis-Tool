#!/usr/bin/env python3
"""
Annotation management system
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import uuid
from dataclasses import dataclass, field
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
from matplotlib.text import Annotation as MplAnnotation

from models.data_models import AnnotationConfig

logger = logging.getLogger(__name__)


class AnnotationManager:
    """Manages plot annotations"""

    def __init__(self):
        self.annotations: Dict[str, AnnotationConfig] = {}
        self.mpl_objects: Dict[str, Any] = {}
        self.axes: Optional[Any] = None

    def add_annotation(self, annotation: AnnotationConfig) -> str:
        """Add an annotation"""
        self.annotations[annotation.id] = annotation
        logger.debug(f"Added annotation: {annotation.id} ({annotation.type})")
        return annotation.id

    def remove_annotation(self, annotation_id: str) -> bool:
        """Remove an annotation"""
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]

            # Remove matplotlib object if exists
            if annotation_id in self.mpl_objects:
                obj = self.mpl_objects[annotation_id]
                try:
                    obj.remove()
                except:
                    pass
                del self.mpl_objects[annotation_id]

            logger.debug(f"Removed annotation: {annotation_id}")
            return True
        return False

    def update_annotation(self, annotation_id: str, **kwargs) -> bool:
        """Update annotation properties"""
        if annotation_id in self.annotations:
            annotation = self.annotations[annotation_id]

            for key, value in kwargs.items():
                if hasattr(annotation, key):
                    setattr(annotation, key, value)

            logger.debug(f"Updated annotation: {annotation_id}")
            return True
        return False

    def get_annotation(self, annotation_id: str) -> Optional[AnnotationConfig]:
        """Get annotation by ID"""
        return self.annotations.get(annotation_id)

    def get_annotations(self) -> Dict[str, AnnotationConfig]:
        """Get all annotations"""
        return self.annotations.copy()

    def set_annotations(self, annotations: Dict[str, AnnotationConfig]):
        """Set all annotations"""
        self.annotations = annotations.copy()

    def clear_annotations(self):
        """Clear all annotations"""
        # Remove matplotlib objects
        for obj in self.mpl_objects.values():
            try:
                obj.remove()
            except:
                pass

        self.annotations.clear()
        self.mpl_objects.clear()
        logger.debug("Cleared all annotations")

    def apply_annotations(self, figure: Any):
        """Apply annotations to a figure"""
        if not figure.axes:
            return

        self.axes = figure.axes[0]

        # Clear existing matplotlib objects
        for obj in self.mpl_objects.values():
            try:
                obj.remove()
            except:
                pass
        self.mpl_objects.clear()

        # Apply each annotation
        for ann_id, annotation in self.annotations.items():
            if not annotation.visible:
                continue

            try:
                mpl_obj = self._create_annotation_object(annotation)
                if mpl_obj:
                    self.mpl_objects[ann_id] = mpl_obj
            except Exception as e:
                logger.error(f"Failed to create annotation {ann_id}: {e}")

    def _create_annotation_object(self, annotation: AnnotationConfig) -> Optional[Any]:
        """Create matplotlib object for annotation"""

        if annotation.type == 'line':
            return self._create_line_annotation(annotation)
        elif annotation.type == 'region':
            return self._create_region_annotation(annotation)
        elif annotation.type == 'text':
            return self._create_text_annotation(annotation)
        elif annotation.type == 'arrow':
            return self._create_arrow_annotation(annotation)
        elif annotation.type == 'point':
            return self._create_point_annotation(annotation)
        else:
            logger.warning(f"Unknown annotation type: {annotation.type}")
            return None

    def _create_line_annotation(self, ann: AnnotationConfig) -> Any:
        """Create line annotation"""
        if ann.x_data is not None:
            # Vertical line
            return self.axes.axvline(
                x=ann.x_data,
                color=ann.color,
                linestyle=ann.line_style,
                linewidth=ann.line_width,
                alpha=ann.alpha,
                label=ann.label if ann.label else None
            )
        elif ann.y_data is not None:
            # Horizontal line
            return self.axes.axhline(
                y=ann.y_data,
                color=ann.color,
                linestyle=ann.line_style,
                linewidth=ann.line_width,
                alpha=ann.alpha,
                label=ann.label if ann.label else None
            )
        return None

    def _create_region_annotation(self, ann: AnnotationConfig) -> Any:
        """Create region annotation"""
        if ann.x_data is not None and ann.x_end is not None:
            # Vertical region
            return self.axes.axvspan(
                ann.x_data, ann.x_end,
                color=ann.color,
                alpha=ann.alpha,
                label=ann.label if ann.label else None
            )
        elif ann.y_data is not None and ann.y_end is not None:
            # Horizontal region
            return self.axes.axhspan(
                ann.y_data, ann.y_end,
                color=ann.color,
                alpha=ann.alpha,
                label=ann.label if ann.label else None
            )
        return None

    def _create_text_annotation(self, ann: AnnotationConfig) -> Any:
        """Create text annotation"""
        if ann.x_data is None or ann.y_data is None or not ann.text:
            return None

        # Create text with optional arrow
        if ann.x_end is not None and ann.y_end is not None:
            # Text with arrow pointing to location
            return self.axes.annotate(
                ann.text,
                xy=(ann.x_data, ann.y_data),
                xytext=(ann.x_end, ann.y_end),
                fontsize=ann.fontsize,
                color=ann.color,
                alpha=ann.alpha,
                arrowprops=dict(
                    arrowstyle='->',
                    color=ann.color,
                    alpha=ann.alpha,
                    linewidth=ann.line_width
                ),
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='white',
                    alpha=0.7
                )
            )
        else:
            # Simple text
            return self.axes.text(
                ann.x_data, ann.y_data,
                ann.text,
                fontsize=ann.fontsize,
                color=ann.color,
                alpha=ann.alpha,
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='white',
                    alpha=0.7
                )
            )

    def _create_arrow_annotation(self, ann: AnnotationConfig) -> Any:
        """Create arrow annotation"""
        if (ann.x_data is None or ann.y_data is None or
                ann.x_end is None or ann.y_end is None):
            return None

        arrow = FancyArrowPatch(
            (ann.x_data, ann.y_data),
            (ann.x_end, ann.y_end),
            arrowstyle='->',
            color=ann.color,
            linewidth=ann.line_width,
            alpha=ann.alpha,
            mutation_scale=20
        )

        self.axes.add_patch(arrow)
        return arrow

    def _create_point_annotation(self, ann: AnnotationConfig) -> Any:
        """Create point annotation"""
        if ann.x_data is None or ann.y_data is None:
            return None

        # Create scatter point
        scatter = self.axes.scatter(
            [ann.x_data], [ann.y_data],
            s=100,
            marker='o',
            color=ann.color,
            alpha=ann.alpha,
            zorder=5,
            edgecolors='black',
            linewidths=1
        )

        # Add label if provided
        if ann.label:
            self.axes.annotate(
                ann.label,
                xy=(ann.x_data, ann.y_data),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=ann.fontsize,
                color=ann.color,
                alpha=ann.alpha
            )

        return scatter

    def find_annotations_at_point(self, x: float, y: float, tolerance: float = 0.05) -> List[str]:
        """Find annotations near a point"""
        found = []

        for ann_id, ann in self.annotations.items():
            if self._is_near_annotation(ann, x, y, tolerance):
                found.append(ann_id)

        return found

    def _is_near_annotation(self, ann: AnnotationConfig, x: float, y: float, tolerance: float) -> bool:
        """Check if point is near annotation"""

        if ann.type == 'point':
            if ann.x_data and ann.y_data:
                dist = np.sqrt((x - ann.x_data) ** 2 + (y - ann.y_data) ** 2)
                return dist < tolerance

        elif ann.type == 'line':
            if ann.x_data is not None:
                return abs(x - ann.x_data) < tolerance
            elif ann.y_data is not None:
                return abs(y - ann.y_data) < tolerance

        elif ann.type == 'region':
            if ann.x_data and ann.x_end:
                return ann.x_data <= x <= ann.x_end
            elif ann.y_data and ann.y_end:
                return ann.y_data <= y <= ann.y_end

        return False

    def export_annotations(self) -> List[Dict[str, Any]]:
        """Export annotations to list of dicts"""
        return [
            {
                'id': ann.id,
                'type': ann.type,
                'label': ann.label,
                'color': ann.color,
                'alpha': ann.alpha,
                'line_width': ann.line_width,
                'line_style': ann.line_style,
                'x_data': ann.x_data,
                'y_data': ann.y_data,
                'x_end': ann.x_end,
                'y_end': ann.y_end,
                'text': ann.text,
                'fontsize': ann.fontsize,
                'visible': ann.visible
            }
            for ann in self.annotations.values()
        ]

    def import_annotations(self, data: List[Dict[str, Any]]):
        """Import annotations from list of dicts"""
        self.clear_annotations()

        for item in data:
            ann = AnnotationConfig(
                type=item['type'],
                label=item.get('label', ''),
                color=item.get('color', 'red'),
                alpha=item.get('alpha', 0.7),
                line_width=item.get('line_width', 2),
                line_style=item.get('line_style', '-'),
                x_data=item.get('x_data'),
                y_data=item.get('y_data'),
                x_end=item.get('x_end'),
                y_end=item.get('y_end'),
                text=item.get('text'),
                fontsize=item.get('fontsize', 10),
                visible=item.get('visible', True)
            )
            self.add_annotation(ann)