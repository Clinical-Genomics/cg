import yaml

from cg.models.balsamic.analysis import parse_balsamic_analysis


def get_balsamic_raw_data():
    """Extracts mock BALSAMIC analysis data"""

    config: dict = yaml.safe_load(open("tests/fixtures/apps/balsamic/case/config.json"))
    metrics: dict = yaml.safe_load(
        open("tests/fixtures/apps/balsamic/case/metrics_deliverables.yaml")
    )

    return config, metrics


class MockBalsamicAnalysis:
    """Mock a BALSAMIC analysis object"""

    @staticmethod
    def get_latest_metadata(_case_id: str):
        """Get the latest metadata of a specific BALSAMIC case"""

        config, metrics = get_balsamic_raw_data()
        return parse_balsamic_analysis(config, metrics)

    @staticmethod
    def get_bundle_deliverables_type(_case_id: str) -> str:
        """Return the analysis type for a case"""

        return "tumor_normal_panel"
