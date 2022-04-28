import yaml

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI


def get_balsamic_raw_data():
    """Extracts mock BALSAMIC analysis data"""

    config: dict = yaml.safe_load(open("tests/fixtures/apps/balsamic/case/config.json"))
    metrics: dict = yaml.safe_load(
        open("tests/fixtures/apps/balsamic/case/metrics_deliverables.yaml")
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
