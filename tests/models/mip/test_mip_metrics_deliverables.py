"""Test MIP metrics deliverables"""
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables, DuplicateReads


def test_instantiate_mip_metrics_deliverables(mip_metrics_deliverables_raw: dict):
    """
    Tests raw data deliverable against a pydantic MetricsDeliverables
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MetricsDeliverables)


def test_mip_metrics_set_duplicate_reads(mip_metrics_deliverables_raw: dict):
    """
    Tests set read duplicates
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that read duplicates was set
    assert metrics_object.duplicate_reads

    duplicate_read: DuplicateReads = metrics_object.duplicate_reads.pop()

    assert isinstance(duplicate_read, DuplicateReads)

    expected_duplicate_read: dict = mip_metrics_deliverables_raw["metrics"].pop()

    # THEN assert that sample id was set
    assert duplicate_read.sample_id == expected_duplicate_read["id"]

    # THEN assert that value was set
    assert duplicate_read.value == float(expected_duplicate_read["value"])
