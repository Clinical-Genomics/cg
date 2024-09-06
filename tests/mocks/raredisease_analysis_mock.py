from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.raredisease.raredisease import MIPMetricsDeliverables

def get_raredisease_raw_data() -> tuple[dict, dict]:
    """Extracts mock RAREDISEASE analysis data."""

    config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML,
        file_path=Path("tests", "fixtures", "apps", "raredisease", "case", "config.json"),
    )
    metrics: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML,
        file_path=Path(
            "tests", "fixtures", "apps", "balsamic", "case", "metrics_deliverables.yaml"
        ),
    )
    return config, metrics


class MockBalsamicAnalysis(BalsamicAnalysisAPI):
    """Mock a BALSAMIC analysis object."""

    def get_latest_metadata(self, case_id: str):
        """Return the latest metadata of a specific BALSAMIC case."""

        config, metrics = get_balsamic_raw_data()
        return self.parse_analysis(config, metrics)

    def get_bundle_deliverables_type(self, case_id: str) -> str:
        """Return the analysis type for a case."""

        return "tumor_normal_panel"
