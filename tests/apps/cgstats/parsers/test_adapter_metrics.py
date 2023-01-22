from pathlib import Path
from cg.apps.cgstats.parsers.adapter_metrics import AdapterMetrics


def test_parse_adapter_metrics(adapter_metrics_path: Path):
    # GIVEN an existing Adapter_Metrics.csv path
    assert adapter_metrics_path.exists()

    # WHEN instantiation a AdapterMetrics obj
    adapter_metrics_obj: AdapterMetrics = AdapterMetrics(adapter_metrics_path)

    # THEN the object should be successfully parsed
    assert adapter_metrics_obj.parse_metrics_file()
