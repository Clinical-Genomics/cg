"""Test MIP metrics deliverables"""
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables


def test_instantiate_mip_metrics_deliverables(mip_metrics_deliverables_raw: dict):
    """
    Tests raw data deliverable against a pydantic MetricsDeliverables
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MipBaseConfig object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MetricsDeliverables)
