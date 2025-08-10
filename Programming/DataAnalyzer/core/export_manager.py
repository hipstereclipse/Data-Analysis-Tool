"""
core/export_manager.py - Export Manager
Handles exporting plots, data, and reports
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import logging
from datetime import datetime

from models.data_models import SeriesConfig, AnnotationConfig
from config.constants import ExportFormats

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Manages export operations
    Handles exporting plots, data, configurations, and reports
    """

    def __init__(self):
        """Initialize export manager"""
        self.default_dpi = 300

    def export_plot(self, figure: plt.Figure, filepath: str,
                    format: ExportFormats = None, dpi: int = None):
        """
        Export a plot to file

        Args:
            figure: Matplotlib figure to export
            filepath: Path to save file
            format: Export format (auto-detected if None)
            dpi: Resolution for raster formats
        """
        try:
            path = Path(filepath)

            # Auto-detect format from extension
            if format is None:
                ext = path.suffix.lower()
                format_map = {
                    '.png': ExportFormats.PNG,
                    '.pdf': ExportFormats.PDF,
                    '.svg': ExportFormats.SVG,
                    '.jpg': ExportFormats.JPG,
                    '.jpeg': ExportFormats.JPG,
                    '.tiff': ExportFormats.TIFF,
                    '.tif': ExportFormats.TIFF,
                    '.eps': ExportFormats.EPS
                }
                format = format_map.get(ext, ExportFormats.PNG)

            # Use format's default DPI if not specified
            if dpi is None:
                dpi = format.default_dpi if format.default_dpi else self.default_dpi

            # Export figure
            figure.savefig(
                filepath,
                format=format.extension,
                dpi=dpi,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )

            logger.info(f"Exported plot to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export plot: {e}")
            raise

    def export_data(self, data: pd.DataFrame, filepath: str, **kwargs):
        """
        Export data to file

        Args:
            data: DataFrame to export
            filepath: Path to save file
            **kwargs: Additional arguments for to_excel/to_csv
        """
        try:
            path = Path(filepath)
            ext = path.suffix.lower()

            if ext in ['.xlsx', '.xls']:
                data.to_excel(filepath, index=False, **kwargs)
            elif ext in ['.csv', '.tsv']:
                delimiter = '\t' if ext == '.tsv' else ','
                data.to_csv(filepath, index=False, sep=delimiter, **kwargs)
            else:
                raise ValueError(f"Unsupported data format: {ext}")

            logger.info(f"Exported data to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise

    def export_series_config(self, series_configs: Dict[str, SeriesConfig],
                             filepath: str):
        """
        Export series configurations to JSON

        Args:
            series_configs: Dictionary of SeriesConfig objects
            filepath: Path to save file
        """
        try:
            config_data = {}
            for series_id, config in series_configs.items():
                config_data[series_id] = config.to_dict()

            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Exported series config to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export series config: {e}")
            raise

    def import_series_config(self, filepath: str) -> Dict[str, SeriesConfig]:
        """
        Import series configurations from JSON

        Args:
            filepath: Path to JSON file

        Returns:
            Dictionary of SeriesConfig objects
        """
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)

            series_configs = {}
            for series_id, data in config_data.items():
                series_configs[series_id] = SeriesConfig.from_dict(data)

            logger.info(f"Imported {len(series_configs)} series from {filepath}")
            return series_configs

        except Exception as e:
            logger.error(f"Failed to import series config: {e}")
            raise

    def export_annotations(self, annotations: List[AnnotationConfig], filepath: str):
        """
        Export annotations to JSON

        Args:
            annotations: List of AnnotationConfig objects
            filepath: Path to save file
        """
        try:
            ann_data = [ann.to_dict() for ann in annotations]

            with open(filepath, 'w') as f:
                json.dump(ann_data, f, indent=2)

            logger.info(f"Exported {len(annotations)} annotations to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export annotations: {e}")
            raise

    def import_annotations(self, filepath: str) -> List[AnnotationConfig]:
        """
        Import annotations from JSON

        Args:
            filepath: Path to JSON file

        Returns:
            List of AnnotationConfig objects
        """
        try:
            with open(filepath, 'r') as f:
                ann_data = json.load(f)

            annotations = [AnnotationConfig.from_dict(data) for data in ann_data]

            logger.info(f"Imported {len(annotations)} annotations from {filepath}")
            return annotations

        except Exception as e:
            logger.error(f"Failed to import annotations: {e}")
            raise

    def export_report(self, filepath: str, figure: plt.Figure = None,
                      summary_text: str = None, data: pd.DataFrame = None,
                      metadata: Dict[str, Any] = None):
        """
        Export a comprehensive report

        Args:
            filepath: Path to save report
            figure: Matplotlib figure to include
            summary_text: Text summary to include
            data: Data table to include
            metadata: Additional metadata
        """
        try:
            path = Path(filepath)
            ext = path.suffix.lower()

            if ext == '.pdf':
                self.export_pdf_report(filepath, figure, summary_text, data, metadata)
            elif ext == '.html':
                self.export_html_report(filepath, figure, summary_text, data, metadata)
            else:
                raise ValueError(f"Unsupported report format: {ext}")

            logger.info(f"Exported report to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            raise

    def export_pdf_report(self, filepath: str, figure: plt.Figure = None,
                          summary_text: str = None, data: pd.DataFrame = None,
                          metadata: Dict[str, Any] = None):
        """Export report as PDF"""
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.figure import Figure

        with PdfPages(filepath) as pdf:
            # Add plot if provided
            if figure:
                pdf.savefig(figure, bbox_inches='tight')

            # Add summary page
            if summary_text:
                fig = Figure(figsize=(8.5, 11))
                ax = fig.add_subplot(111)
                ax.axis('off')

                # Add title
                title = metadata.get('title', 'Analysis Report') if metadata else 'Analysis Report'
                ax.text(0.5, 0.95, title, transform=ax.transAxes,
                        fontsize=16, fontweight='bold', ha='center')

                # Add date
                date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ax.text(0.5, 0.92, date_str, transform=ax.transAxes,
                        fontsize=10, ha='center')

                # Add summary text
                ax.text(0.05, 0.85, summary_text, transform=ax.transAxes,
                        fontsize=10, verticalalignment='top', fontfamily='monospace')

                pdf.savefig(fig, bbox_inches='tight')

            # Add metadata
            d = pdf.infodict()
            d['Title'] = metadata.get('title', 'Analysis Report') if metadata else 'Analysis Report'
            d['Author'] = metadata.get('author', 'Excel Data Plotter') if metadata else 'Excel Data Plotter'
            d['Subject'] = metadata.get('subject', 'Data Analysis') if metadata else 'Data Analysis'
            d['Keywords'] = metadata.get('keywords', '') if metadata else ''
            d['CreationDate'] = datetime.now()

    def export_html_report(self, filepath: str, figure: plt.Figure = None,
                           summary_text: str = None, data: pd.DataFrame = None,
                           metadata: Dict[str, Any] = None):
        """Export report as HTML"""
        import base64
        from io import BytesIO

        html_parts = []

        # HTML header
        title = metadata.get('title', 'Analysis Report') if metadata else 'Analysis Report'
        html_parts.append(f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                pre {{ background-color: #f0f0f0; padding: 10px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metadata {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p class="metadata">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """)

        # Add plot if provided
        if figure:
            # Convert figure to base64 image
            buffer = BytesIO()
            figure.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()

            html_parts.append(f"""
            <h2>Plot</h2>
            <img src="data:image/png;base64,{img_base64}" style="max-width: 100%;">
            """)

        # Add summary if provided
        if summary_text:
            html_parts.append(f"""
            <h2>Summary</h2>
            <pre>{summary_text}</pre>
            """)

        # Add data table if provided
        if data is not None and not data.empty:
            html_parts.append(f"""
            <h2>Data</h2>
            {data.to_html(index=False, table_id="data-table")}
            """)

        # HTML footer
        html_parts.append("""
        </body>
        </html>
        """)

        # Write HTML file
        with open(filepath, 'w') as f:
            f.write('\n'.join(html_parts))

    def export_all_data(self, loaded_files: Dict[str, Any],
                        series_configs: Dict[str, SeriesConfig],
                        filepath: str):
        """
        Export all loaded data and configurations

        Args:
            loaded_files: Dictionary of loaded FileData objects
            series_configs: Dictionary of SeriesConfig objects
            filepath: Base filepath for export
        """
        try:
            path = Path(filepath)
            base_path = path.parent
            base_name = path.stem

            # Create export directory
            export_dir = base_path / f"{base_name}_export"
            export_dir.mkdir(exist_ok=True)

            # Export each file's data
            for file_id, file_data in loaded_files.items():
                file_path = export_dir / f"{file_data.filename}"
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    file_data.data.to_excel(file_path, index=False)
                else:
                    file_data.data.to_csv(file_path, index=False)

            # Export series configurations
            config_path = export_dir / "series_config.json"
            self.export_series_config(series_configs, str(config_path))

            # Create summary file
            summary_path = export_dir / "summary.txt"
            with open(summary_path, 'w') as f:
                f.write(f"Export Summary\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Files Exported: {len(loaded_files)}\n")
                f.write(f"Series Configured: {len(series_configs)}\n\n")

                f.write("Files:\n")
                for file_id, file_data in loaded_files.items():
                    f.write(
                        f"  - {file_data.filename} ({file_data.row_count} rows, {file_data.column_count} columns)\n")

                f.write("\nSeries:\n")
                for series_id, config in series_configs.items():
                    f.write(f"  - {config.name}: {config.x_column} vs {config.y_column}\n")

            logger.info(f"Exported all data to {export_dir}")

        except Exception as e:
            logger.error(f"Failed to export all data: {e}")
            raise