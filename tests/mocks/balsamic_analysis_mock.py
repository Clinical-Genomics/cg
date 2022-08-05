from pathlib import Path
from typing import Tuple

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI


def get_balsamic_raw_data() -> Tuple[dict, dict]:
    """Extracts mock BALSAMIC analysis data"""

    config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML,
        file_path=Path("tests", "fixtures", "apps", "balsamic", "case", "config.json"),
    )
    metrics: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML,
        file_path=Path(
            "tests", "fixtures", "apps", "balsamic", "case", "metrics_deliverables.yaml"
        ),
    )
    return config, metrics


class MockBalsamicAnalysis(BalsamicAnalysisAPI):
    """Mock a BALSAMIC analysis object"""

    def get_latest_metadata(self, case_id: str):
        """Get the latest metadata of a specific BALSAMIC case"""

        config, metrics = get_balsamic_raw_data()
        return self.parse_analysis(config, metrics)

    def get_bundle_deliverables_type(self, case_id: str) -> str:
        """Return the analysis type for a case"""

        return "tumor_normal_panel"
