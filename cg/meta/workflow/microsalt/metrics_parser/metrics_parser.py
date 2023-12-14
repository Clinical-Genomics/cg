from pathlib import Path

from cg.io.json import read_json
from .models import QualityMetrics


class MetricsParser:
    @staticmethod
    def parse(file_path: Path) -> QualityMetrics:
        data = read_json(file_path)
        formatted_data = {"samples": data}
        return QualityMetrics.model_validate(formatted_data)
