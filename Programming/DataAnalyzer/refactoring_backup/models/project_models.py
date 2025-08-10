#!/usr/bin/env python3
"""
models/project_models.py - Complete Project Models Implementation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import json
from pathlib import Path

from models.data_models import FileData, SeriesConfig, AnnotationConfig


@dataclass
class ProjectMetadata:
    """
    Metadata for a project file
    Used for quick loading of project information without full deserialization
    """
    name: str = "Untitled Project"
    description: str = ""
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    author: str = ""

    # Quick stats
    file_count: int = 0
    series_count: int = 0
    annotation_count: int = 0

    # File info
    project_path: Optional[str] = None
    file_size: int = 0

    # Thumbnail/preview data
    thumbnail: Optional[bytes] = None
    preview_data: Dict[str, Any] = field(default_factory=dict)

    # Tags and categories
    tags: List[str] = field(default_factory=list)
    category: str = "General"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'author': self.author,
            'file_count': self.file_count,
            'series_count': self.series_count,
            'annotation_count': self.annotation_count,
            'project_path': self.project_path,
            'file_size': self.file_size,
            'tags': self.tags,
            'category': self.category,
            'preview_data': self.preview_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """Create from dictionary"""
        metadata = cls()

        if 'name' in data:
            metadata.name = data['name']
        if 'description' in data:
            metadata.description = data['description']
        if 'version' in data:
            metadata.version = data['version']
        if 'created_at' in data:
            metadata.created_at = datetime.fromisoformat(data['created_at'])
        if 'modified_at' in data:
            metadata.modified_at = datetime.fromisoformat(data['modified_at'])
        if 'author' in data:
            metadata.author = data['author']
        if 'file_count' in data:
            metadata.file_count = data['file_count']
        if 'series_count' in data:
            metadata.series_count = data['series_count']
        if 'annotation_count' in data:
            metadata.annotation_count = data['annotation_count']
        if 'project_path' in data:
            metadata.project_path = data['project_path']
        if 'file_size' in data:
            metadata.file_size = data['file_size']
        if 'tags' in data:
            metadata.tags = data['tags']
        if 'category' in data:
            metadata.category = data['category']
        if 'preview_data' in data:
            metadata.preview_data = data['preview_data']

        return metadata


@dataclass
class Project:
    """Represents a complete project with all data and configurations"""

    name: str = "Untitled Project"
    description: str = ""

    # Project data
    files: Dict[str, FileData] = field(default_factory=dict)
    series: Dict[str, SeriesConfig] = field(default_factory=dict)
    annotations: Dict[str, AnnotationConfig] = field(default_factory=dict)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    tags: List[str] = field(default_factory=list)

    # Additional metadata from first version
    author_email: str = ""
    project_path: Optional[str] = None
    auto_save: bool = True
    auto_save_interval: int = 300  # seconds
    category: str = "General"

    def add_file(self, file_data: FileData) -> str:
        """Add a file to the project"""
        if not file_data.id:
            file_data.id = str(uuid.uuid4())

        self.files[file_data.id] = file_data
        self.modified_at = datetime.now()
        return file_data.id

    def remove_file(self, file_id: str):
        """Remove a file and associated series"""
        if file_id in self.files:
            # Remove associated series
            series_to_remove = [
                sid for sid, series in self.series.items()
                if series.file_id == file_id
            ]
            for sid in series_to_remove:
                del self.series[sid]

            # Remove file
            del self.files[file_id]
            self.modified_at = datetime.now()

    def add_series(self, series: SeriesConfig) -> str:
        """Add a series to the project"""
        if not series.id:
            series.id = str(uuid.uuid4())

        self.series[series.id] = series
        self.modified_at = datetime.now()
        return series.id

    def remove_series(self, series_id: str):
        """Remove a series from the project"""
        if series_id in self.series:
            del self.series[series_id]
            self.modified_at = datetime.now()

    def add_annotation(self, annotation: AnnotationConfig) -> str:
        """Add an annotation to the project"""
        if not annotation.id:
            annotation.id = str(uuid.uuid4())

        self.annotations[annotation.id] = annotation
        self.modified_at = datetime.now()
        return annotation.id

    def remove_annotation(self, annotation_id: str):
        """Remove an annotation from the project"""
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]
            self.modified_at = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        total_rows = sum(f.metadata.get('rows', 0) for f in self.files.values())
        total_columns = sum(f.metadata.get('columns', 0) for f in self.files.values())
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

    def get_metadata(self) -> ProjectMetadata:
        """Generate project metadata"""
        stats = self.get_statistics()

        metadata = ProjectMetadata(
            name=self.name,
            description=self.description,
            version=self.version,
            created_at=self.created_at,
            modified_at=self.modified_at,
            author=self.author,
            file_count=stats['file_count'],
            series_count=stats['series_count'],
            annotation_count=stats['annotation_count'],
            project_path=self.project_path,
            tags=self.tags.copy(),
            category=self.category
        )

        # Add preview data
        metadata.preview_data = {
            'visible_series': stats['visible_series'],
            'total_rows': stats['total_rows'],
            'total_columns': stats['total_columns']
        }

        return metadata

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'project_id': self.project_id,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'author': self.author,
            'author_email': self.author_email,
            'project_path': self.project_path,
            'auto_save': self.auto_save,
            'auto_save_interval': self.auto_save_interval,
            'tags': self.tags,
            'category': self.category,
            'config': self.config,
            'files': {fid: f.to_dict() for fid, f in self.files.items()},
            'series': {sid: s.to_dict() for sid, s in self.series.items()},
            'annotations': {aid: a.to_dict() for aid, a in self.annotations.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary"""
        project = cls()

        # Set basic properties
        for field in ['name', 'description', 'project_id', 'version',
                      'author', 'author_email', 'project_path',
                      'auto_save', 'auto_save_interval', 'category', 'tags', 'config']:
            if field in data:
                setattr(project, field, data[field])

        # Set datetime fields
        if 'created_at' in data:
            project.created_at = datetime.fromisoformat(data['created_at'])
        if 'modified_at' in data:
            project.modified_at = datetime.fromisoformat(data['modified_at'])

        # Reconstruct nested objects (implementation depends on from_dict methods in other classes)
        # Placeholder for actual deserialization logic
        project.files = {fid: FileData.from_dict(fdata) for fid, fdata in data.get('files', {}).items()}
        project.series = {sid: SeriesConfig.from_dict(sdata) for sid, sdata in data.get('series', {}).items()}
        project.annotations = {aid: AnnotationConfig.from_dict(adata) for aid, adata in
                               data.get('annotations', {}).items()}

        return project


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

@dataclass
class RecentProjects:
    """Manages recently opened projects"""
    max_recent: int = 10
    projects: List[Dict[str, Any]] = field(default_factory=list)

    def add_project(self, project_path: str, project_name: str):
        """Add a project to recent list"""
        # Remove if already exists
        self.projects = [p for p in self.projects if p['path'] != project_path]

        # Add to front
        self.projects.insert(0, {
            'path': project_path,
            'name': project_name,
            'last_opened': datetime.now().isoformat()
        })

        # Limit size
        self.projects = self.projects[:self.max_recent]

    def get_recent(self) -> List[Dict[str, Any]]:
        """Get recent projects list"""
        return self.projects.copy()

    def clear(self):
        """Clear recent projects"""
        self.projects = []

    def save(self, filepath: str):
        """Save recent projects to file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.projects, f, indent=2)

    def load(self, filepath: str):
        """Load recent projects from file"""
        import json
        try:
            with open(filepath, 'r') as f:
                self.projects = json.load(f)
        except:
            self.projects = []
