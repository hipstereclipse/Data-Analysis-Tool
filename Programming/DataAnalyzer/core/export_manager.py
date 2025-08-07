#!/usr/bin/env python3
"""
Export functionality for various formats
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json
import csv

logger = logging.getLogger(__name__)


class ExportManager:
    """Manages data and plot export"""

    def __init__(self):
        self.supported_formats = {
            'image': ['.png', '.pdf', '.svg', '.jpg'],
            'data': ['.csv', '.xlsx', '.json', '.txt'],
            'report': ['.html', '.pdf', '.docx']
        }

    def export_plot(
            self,
            figure: Any,
            filepath: str,
            dpi: int = 300,
            transparent: bool = False
    ):
        """
        Export plot to image file

        Args:
            figure: Matplotlib figure
            filepath: Target file path
            dpi: Resolution in dots per inch
            transparent: Whether to use transparent background
        """
        filepath = Path(filepath)

        try:
            figure.savefig(
                filepath,
                dpi=dpi,
                bbox_inches='tight',
                transparent=transparent,
                facecolor='white' if not transparent else 'none'
            )
            logger.info(f"Plot exported to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to export plot: {e}")
            raise

    def export_data(
            self,
            data: pd.DataFrame,
            filepath: str,
            **kwargs
    ):
        """
        Export data to file

        Args:
            data: DataFrame to export
            filepath: Target file path
            **kwargs: Additional format-specific options
        """
        filepath = Path(filepath)
        ext = filepath.suffix.lower()

        try:
            if ext == '.csv':
                self._export_csv(data, filepath, **kwargs)
            elif ext in ['.xlsx', '.xls']:
                self._export_excel(data, filepath, **kwargs)
            elif ext == '.json':
                self._export_json(data, filepath, **kwargs)
            elif ext == '.txt':
                self._export_text(data, filepath, **kwargs)
            else:
                raise ValueError(f"Unsupported export format: {ext}")

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise

    def _export_csv(self, data: pd.DataFrame, filepath: Path, **kwargs):
        """Export to CSV"""
        data.to_csv(
            filepath,
            index=kwargs.get('include_index', False),
            encoding=kwargs.get('encoding', 'utf-8'),
            sep=kwargs.get('separator', ',')
        )
        logger.info(f"Data exported to CSV: {filepath}")

    def _export_excel(self, data: pd.DataFrame, filepath: Path, **kwargs):
        """Export to Excel"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            sheet_name = kwargs.get('sheet_name', 'Data')
            data.to_excel(
                writer,
                sheet_name=sheet_name,
                index=kwargs.get('include_index', False)
            )

            # Auto-adjust column widths
            if kwargs.get('auto_column_width', True):
                worksheet = writer.sheets[sheet_name]
                for column in data:
                    column_length = max(
                        data[column].astype(str).map(len).max(),
                        len(str(column))
                    )
                    col_idx = data.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2

        logger.info(f"Data exported to Excel: {filepath}")

    def _export_json(self, data: pd.DataFrame, filepath: Path, **kwargs):
        """Export to JSON"""
        orient = kwargs.get('orient', 'records')
        with open(filepath, 'w', encoding='utf-8') as f:
            data.to_json(f, orient=orient, indent=2)
        logger.info(f"Data exported to JSON: {filepath}")

    def _export_text(self, data: pd.DataFrame, filepath: Path, **kwargs):
        """Export to text file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data.to_string(
                index=kwargs.get('include_index', False)
            ))
        logger.info(f"Data exported to text: {filepath}")

    def export_report(
            self,
            report_data: Dict[str, Any],
            filepath: str,
            template: Optional[str] = None
    ):
        """
        Export analysis report

        Args:
            report_data: Report data dictionary
            filepath: Target file path
            template: Optional template name
        """
        filepath = Path(filepath)
        ext = filepath.suffix.lower()

        if ext == '.html':
            self._export_html_report(report_data, filepath, template)
        elif ext == '.txt':
            self._export_text_report(report_data, filepath)
        else:
            raise ValueError(f"Unsupported report format: {ext}")

    def _export_html_report(
            self,
            report_data: Dict[str, Any],
            filepath: Path,
            template: Optional[str] = None
    ):
        """Export HTML report"""
        html_content = self._generate_html_report(report_data, template)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Report exported to HTML: {filepath}")

    def _export_text_report(self, report_data: Dict[str, Any], filepath: Path):
        """Export text report"""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append(report_data.get('title', 'Analysis Report'))
        lines.append(f"Generated: {datetime.now()}")
        lines.append("=" * 70)
        lines.append("")

        # Sections
        for section_name, section_data in report_data.items():
            if section_name in ['title', 'metadata']:
                continue

            lines.append(f"\n{section_name.upper()}")
            lines.append("-" * 40)

            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    lines.append(f"  {key}: {value}")
            elif isinstance(section_data, list):
                for item in section_data:
                    lines.append(f"  • {item}")
            else:
                lines.append(str(section_data))

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        logger.info(f"Report exported to text: {filepath}")

    def _generate_html_report(
            self,
            report_data: Dict[str, Any],
            template: Optional[str] = None
    ) -> str:
        """Generate HTML report content"""

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #3B82F6; }}
                .metric-label {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Generated: {timestamp}</p>
            {content}
        </body>
        </html>
        """

        content = []

        for section_name, section_data in report_data.items():
            if section_name in ['title', 'metadata']:
                continue

            content.append(f"<h2>{section_name}</h2>")

            if isinstance(section_data, dict):
                content.append("<table>")
                for key, value in section_data.items():
                    content.append(f"<tr><th>{key}</th><td>{value}</td></tr>")
                content.append("</table>")
            elif isinstance(section_data, list):
                content.append("<ul>")
                for item in section_data:
                    content.append(f"<li>{item}</li>")
                content.append("</ul>")
            else:
                content.append(f"<p>{section_data}</p>")

        return html.format(
            title=report_data.get('title', 'Analysis Report'),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            content='\n'.join(content)
        )