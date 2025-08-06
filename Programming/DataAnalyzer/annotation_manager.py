#!/usr/bin/env python3
"""
annotation_manager.py - Annotation management system for plots
Handles adding, editing, and removing annotations on plots
"""

import uuid  # For generating unique IDs
import json  # For import/export functionality
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch  # For drawing shapes
from matplotlib.lines import Line2D  # For line annotations


class AnnotationManager:
    """
    Manages all annotations for a plot
    Provides methods to add, update, remove, and draw annotations
    """

    def __init__(self):
        """Initialize empty annotation manager"""
        # Dictionary to store all annotations by ID
        self.annotations = {}

        # Counter for generating unique IDs
        self.annotation_id_counter = 0

        # Currently selected annotation for editing
        self.selected_annotation = None

    def add_annotation(self, ann_type, **kwargs):
        """
        Add a new annotation to the manager

        Args:
            ann_type (str): Type of annotation ('vline', 'hline', 'region', 'text', 'point', 'arrow')
            **kwargs: Additional parameters specific to annotation type

        Returns:
            str: ID of the created annotation
        """
        # Generate unique ID
        self.annotation_id_counter += 1
        ann_id = f"ann_{self.annotation_id_counter}"

        # Create annotation dictionary with defaults
        annotation = {
            'id': ann_id,  # Unique identifier
            'type': ann_type,  # Annotation type
            'visible': True,  # Whether to display
            'editable': True,  # Whether user can edit
            **kwargs  # Add all provided parameters
        }

        # Store annotation
        self.annotations[ann_id] = annotation

        return ann_id

    def update_annotation(self, ann_id, **kwargs):
        """
        Update properties of an existing annotation

        Args:
            ann_id (str): ID of annotation to update
            **kwargs: Properties to update
        """
        # Check if annotation exists
        if ann_id in self.annotations:
            # Update specified properties
            self.annotations[ann_id].update(kwargs)

    def remove_annotation(self, ann_id):
        """
        Remove an annotation by ID

        Args:
            ann_id (str): ID of annotation to remove
        """
        # Check if annotation exists
        if ann_id in self.annotations:
            # Delete annotation
            del self.annotations[ann_id]

            # Clear selection if this was selected
            if self.selected_annotation == ann_id:
                self.selected_annotation = None

    def clear_all(self):
        """Remove all annotations"""
        self.annotations.clear()  # Clear dictionary
        self.selected_annotation = None  # Clear selection
        self.annotation_id_counter = 0  # Reset counter

    def select_annotation(self, ann_id):
        """
        Select an annotation for editing

        Args:
            ann_id (str): ID of annotation to select
        """
        # Set as selected if it exists
        if ann_id in self.annotations:
            self.selected_annotation = ann_id

    def deselect_annotation(self):
        """Deselect current annotation"""
        self.selected_annotation = None

    def get_annotation(self, ann_id):
        """
        Get annotation data by ID

        Args:
            ann_id (str): Annotation ID

        Returns:
            dict: Annotation data or None if not found
        """
        return self.annotations.get(ann_id)

    def get_visible_annotations(self):
        """
        Get list of visible annotations

        Returns:
            list: List of visible annotation dictionaries
        """
        # Filter for visible annotations
        return [ann for ann in self.annotations.values() if ann.get('visible', True)]

    def draw_annotations(self, ax, picker=True):
        """
        Draw all visible annotations on the given axes

        Args:
            ax: Matplotlib axes object
            picker (bool): Whether to enable picking (for interaction)

        Returns:
            dict: Dictionary mapping artists to annotation IDs
        """
        # Dictionary to map drawn artists to annotation IDs
        artists = {}

        # Draw each visible annotation
        for ann_id, ann in self.annotations.items():
            # Skip invisible annotations
            if not ann.get('visible', True):
                continue

            # Variable to store created artist
            artist = None

            # Draw based on annotation type
            if ann['type'] == 'vline':
                # Vertical line annotation
                artist = ax.axvline(
                    x=ann['x_pos'],  # X position
                    color=ann.get('color', 'red'),  # Line color
                    linestyle=ann.get('style', '--'),  # Line style
                    linewidth=ann.get('width', 2),  # Line width
                    alpha=ann.get('alpha', 0.8),  # Transparency
                    label=ann.get('label'),  # Legend label
                    picker=picker  # Enable picking
                )

            elif ann['type'] == 'hline':
                # Horizontal line annotation
                artist = ax.axhline(
                    y=ann['y_pos'],  # Y position
                    color=ann.get('color', 'blue'),  # Line color
                    linestyle=ann.get('style', '--'),  # Line style
                    linewidth=ann.get('width', 2),  # Line width
                    alpha=ann.get('alpha', 0.8),  # Transparency
                    label=ann.get('label'),  # Legend label
                    picker=picker  # Enable picking
                )

            elif ann['type'] == 'region':
                # Shaded region annotation
                artist = ax.axvspan(
                    ann['x_start'],  # Start X position
                    ann['x_end'],  # End X position
                    color=ann.get('color', 'yellow'),  # Fill color
                    alpha=ann.get('alpha', 0.3),  # Transparency
                    label=ann.get('label'),  # Legend label
                    picker=picker  # Enable picking
                )

            elif ann['type'] == 'point':
                # Point marker annotation
                artist = ax.scatter(
                    ann['x_pos'],  # X position
                    ann['y_pos'],  # Y position
                    marker=ann.get('marker', 'o'),  # Marker style
                    s=ann.get('size', 100),  # Marker size
                    color=ann.get('color', 'red'),  # Marker color
                    edgecolors='black' if ann_id == self.selected_annotation else 'none',  # Highlight if selected
                    linewidths=2 if ann_id == self.selected_annotation else 0,  # Edge width
                    zorder=10,  # Draw order (on top)
                    label=ann.get('label'),  # Legend label
                    picker=picker  # Enable picking
                )

            elif ann['type'] == 'text':
                # Text annotation
                # Get text box properties if specified
                bbox_props = ann.get('bbox')

                # Highlight selected annotation
                if ann_id == self.selected_annotation and bbox_props:
                    bbox_props = dict(bbox_props)  # Copy to avoid modifying original
                    bbox_props['edgecolor'] = 'blue'  # Highlight border
                    bbox_props['linewidth'] = 2  # Thicker border

                # Create text annotation
                artist = ax.text(
                    ann['x_pos'],  # X position
                    ann['y_pos'],  # Y position
                    ann['text'],  # Text content
                    fontsize=ann.get('fontsize', 12),  # Font size
                    color=ann.get('color', 'black'),  # Text color
                    bbox=bbox_props,  # Background box
                    zorder=10,  # Draw order
                    picker=picker  # Enable picking
                )

            elif ann['type'] == 'arrow':
                # Arrow annotation with fancy arrow patch
                arrow = FancyArrowPatch(
                    (ann['x_start'], ann['y_start']),  # Start point
                    (ann['x_end'], ann['y_end']),  # End point
                    arrowstyle=ann.get('style', '->'),  # Arrow style
                    color=ann.get('color', 'black'),  # Arrow color
                    linewidth=ann.get('width', 2),  # Line width
                    mutation_scale=20,  # Arrow head size
                    alpha=ann.get('alpha', 0.8)  # Transparency
                )
                ax.add_patch(arrow)  # Add to axes
                artist = arrow

            # Store artist-annotation mapping
            if artist:
                artists[artist] = ann_id

        return artists

    def export_annotations(self, filename):
        """
        Export annotations to JSON file

        Args:
            filename (str): Path to save file
        """
        # Prepare data for export
        export_data = {
            'version': '1.0',  # Format version
            'annotations': self.annotations,  # All annotations
            'selected': self.selected_annotation,  # Current selection
            'counter': self.annotation_id_counter  # ID counter state
        }

        # Write to JSON file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_annotations(self, filename, merge=False):
        """
        Import annotations from JSON file

        Args:
            filename (str): Path to load file
            merge (bool): Whether to merge with existing annotations
        """
        # Load from JSON file
        with open(filename, 'r') as f:
            import_data = json.load(f)

        # Clear existing if not merging
        if not merge:
            self.clear_all()

        # Import annotations
        for ann_id, annotation in import_data.get('annotations', {}).items():
            if merge:
                # Generate new ID for merged annotations
                new_id = self.add_annotation(
                    annotation['type'],
                    **{k: v for k, v in annotation.items() if k not in ['id', 'type']}
                )
            else:
                # Use original ID
                self.annotations[ann_id] = annotation

        # Restore counter state if not merging
        if not merge:
            self.annotation_id_counter = import_data.get('counter', 0)
            self.selected_annotation = import_data.get('selected')

    def create_vacuum_templates(self):
        """
        Create common vacuum analysis annotation templates

        Returns:
            list: List of created annotation IDs
        """
        created_ids = []

        # Base pressure line template
        ann_id = self.add_annotation(
            'hline',
            y_pos=1e-6,  # Typical base pressure
            label="Base Pressure",
            color='green',
            style='--',
            width=2,
            alpha=0.8
        )
        created_ids.append(ann_id)

        # Pressure target lines
        targets = [
            (1e-3, "High Vacuum", 'blue'),
            (1e-6, "Ultra-High Vacuum", 'green'),
            (1e-9, "Extreme High Vacuum", 'purple')
        ]

        for pressure, label, color in targets:
            ann_id = self.add_annotation(
                'hline',
                y_pos=pressure,
                label=f"{label}: {pressure:.0e} mbar",
                color=color,
                style=':',
                width=1.5,
                alpha=0.6
            )
            created_ids.append(ann_id)

        return created_ids

    def find_annotations_at_point(self, x, y, tolerance=0.05):
        """
        Find annotations near a given point (for interaction)

        Args:
            x: X coordinate
            y: Y coordinate
            tolerance: Distance tolerance for selection

        Returns:
            list: List of annotation IDs near the point
        """
        found = []

        for ann_id, ann in self.annotations.items():
            # Check based on annotation type
            if ann['type'] == 'vline':
                # Check X distance for vertical lines
                if abs(ann['x_pos'] - x) < tolerance:
                    found.append(ann_id)

            elif ann['type'] == 'hline':
                # Check Y distance for horizontal lines
                if abs(ann['y_pos'] - y) < tolerance:
                    found.append(ann_id)

            elif ann['type'] == 'region':
                # Check if point is inside region
                if ann['x_start'] <= x <= ann['x_end']:
                    found.append(ann_id)

            elif ann['type'] == 'point':
                # Check distance to point
                dist = ((ann['x_pos'] - x) ** 2 + (ann['y_pos'] - y) ** 2) ** 0.5
                if dist < tolerance:
                    found.append(ann_id)

            elif ann['type'] == 'text':
                # Check if near text position
                dist = ((ann['x_pos'] - x) ** 2 + (ann['y_pos'] - y) ** 2) ** 0.5
                if dist < tolerance:
                    found.append(ann_id)

        return found

    def move_annotation(self, ann_id, dx=0, dy=0):
        """
        Move an annotation by a delta amount

        Args:
            ann_id (str): Annotation ID
            dx: X-axis movement
            dy: Y-axis movement
        """
        ann = self.annotations.get(ann_id)
        if not ann:
            return

        # Move based on type
        if ann['type'] == 'vline':
            ann['x_pos'] += dx

        elif ann['type'] == 'hline':
            ann['y_pos'] += dy

        elif ann['type'] == 'region':
            ann['x_start'] += dx
            ann['x_end'] += dx

        elif ann['type'] in ['point', 'text']:
            ann['x_pos'] += dx
            ann['y_pos'] += dy

        elif ann['type'] == 'arrow':
            ann['x_start'] += dx
            ann['y_start'] += dy
            ann['x_end'] += dx
            ann['y_end'] += dy