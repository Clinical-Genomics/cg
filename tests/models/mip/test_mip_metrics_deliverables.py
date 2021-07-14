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


def test_mip_metrics_set_duplicates(mip_metrics_deliverables_raw: dict):
    """
    Tests set duplicates
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MipBaseConfig object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that metric duplictaes is a dict
    assert isinstance(metrics_object.duplicates, dict)

    # When having a single sample
    duplicates = {
        "another_id": 0.09,
        "an_id": 0.0748899652117993,
    }

    # THEN assert that duplicates are set
    assert metrics_object.duplicates == duplicates
