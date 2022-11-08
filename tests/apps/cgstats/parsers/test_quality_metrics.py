from pathlib import Path
from cg.apps.cgstats.parsers.quality_metrics import QualityMetrics


def test_parse_quality_metrics(quality_metrics_path: Path):
    # GIVEN an existing Quality_Metrics.csv path
    assert quality_metrics_path.exists()

    # WHEN instantiation a QualityMetrics obj
    quality_metrics_obj: QualityMetrics = QualityMetrics(quality_metrics_path)

    # THEN the object should be successfully parsed
    assert quality_metrics_obj.parse_metrics_file()
