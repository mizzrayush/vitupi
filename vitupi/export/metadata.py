"""
Machine-readable JSON reporting module.
"""

import json
import os
from vitupi.models import ExtractionResult


def export_json_report(result: ExtractionResult, output_dir: str, filename: str = "vitupi_report.json") -> str:
    """Save an extraction result report to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, filename)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    result.report_path = report_path
    return report_path
