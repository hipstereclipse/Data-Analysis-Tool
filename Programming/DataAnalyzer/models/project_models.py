# !/usr/bin/env python3
"""
Project-related data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

from models.data_models import FileData, SeriesConfig, AnnotationConfig


@dataclass
class Project:
    """Represents a complete project"""

    name: str = "Untitled Project"
    description: str = ""

    # Project data
    files: Dict[str, FileData] = field(default_factory=dict)
    series: Dict[str, SeriesConfig] = field(default_factory=dict)
    annotations: Dict[str, AnnotationConfig] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    tags: List[str] = field(default_factory=list)

    def add_file(self, file_data: FileData):
        """Add a file to the project"""
        self.files[file_data.id] = file_data
        self.modified_at = datetime.now()

    def remove_file(self, file_id: str):
        """Remove a file from the project"""
        if file_id in self.files:
            del self.files[file_id]

            # Remove associated series
            series_to_remove = [
                sid for sid, s in self.series.items()
                if s.file_id == file_id
            ]
            for sid in series_to_remove:
                del self.series[sid]

            self.modified_at = datetime.now()

    def add_series(self, series: SeriesConfig):
        """Add a series to the project"""
        self.series[series.id] = series
        self.modified_at = datetime.now()

    def remove_series(self, series_id: str):
        """Remove a series from the project"""
        if series_id in self.series:
            del self.series[series_id]
            self.modified_at = datetime.now()

    def add_annotation(self, annotation: AnnotationConfig):
        """Add an annotation to the project"""
        self.annotations[annotation.id] = annotation
        self.modified_at = datetime.now()

    def remove_annotation(self, annotation_id: str):
        """Remove an annotation from the project"""
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]
            self.modified_at = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        total_rows = sum(f.metadata['rows'] for f in self.files.values())
        total_columns = sum(f.metadata['columns'] for f in self.files.values())
        visible_series = sum(1 for s in self.series.values() if s.visible)

        return {
            'file_count': len(self.files),
            'series_count': len(self.series),
            'visible_series': visible_series,
            'annotation_count': len(self.annotations),
            'total_rows': total_rows,
            'total_columns': total_columns,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }

    def validate(self) -> List[str]:
        """Validate project integrity"""
        errors = []

        # Check series references
        for series in self.series.values():
            if series.file_id not in self.files:
                errors.append(f"Series '{series.name}' references missing file")

        # Check for empty project
        if not self.files:
            errors.append("No files loaded")

        if not self.series:
            errors.append("No series defined")

        return errors


@dataclass
class ProjectTemplate:
    """Template for creating new projects"""

    name: str
    description: str
    default_config: Dict[str, Any] = field(default_factory=dict)
    sample_files: List[str] = field(default_factory=list)
    sample_series: List[Dict[str, Any]] = field(default_factory=list)

    def create_project(self) -> Project:
        """Create a new project from template"""
        project = Project(
            name=self.name,
            description=self.description,
            config=self.default_config.copy()
        )

        # Add sample series configurations if provided
        # (actual file loading would be done by the application)

        return project
