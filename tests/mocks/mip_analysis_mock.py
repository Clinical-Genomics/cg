import yaml

from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables


def create_mip_metrics_deliverables():
    """Get an mip_metrics_deliverables object"""
    metrics_deliverables: dict = yaml.safe_load(
        open("tests/fixtures/apps/mip/case_metrics_deliverables.yaml")
    )
    return MetricsDeliverables(**metrics_deliverables)


class MockMipAnalysis:
    """Mock an MIP analysis object"""

    def panel(self, case_obj) -> [str]:
        """Create the aggregated panel file"""
        return [""]

    @staticmethod
    def get_latest_metadata(family_id=None):
        """Mock get_latest_metadata"""
        # Returns: dict: parsed data
        # Define output dict
        metrics: MetricsDeliverables = create_mip_metrics_deliverables()
        out_data = {
            "case": family_id or "yellowhog",
            "genome_build": "hg19",
            "id_metrics": metrics.id_metrics,
            "mip_version": "v4.0.20",
            "rank_model_version": "1.18",
            "sample_ids": ["2018-20203", "2018-20204"],
            "sv_rank_model_version": "1.08",
        }
        return out_data

    @staticmethod
    def convert_panels(customer_id, panels):
        """Mock convert_panels"""
        _ = customer_id, panels
        return ""
