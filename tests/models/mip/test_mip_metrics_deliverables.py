"""Test MIP metrics deliverables"""

from cg.models.mip.mip_metrics_deliverables import (
    MetricsDeliverables,
    DuplicateReads,
    ParsedMetrics,
    GenderCheck,
    MeanInsertSize,
    MappedReads,
    get_id_metric,
)


def test_instantiate_mip_metrics_deliverables(mip_metrics_deliverables_raw: dict):
    """
    Tests raw data deliverable against a pydantic MetricsDeliverables
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MetricsDeliverables)


def test_instantiate_mip_metrics_ids(mip_metrics_deliverables_raw: dict):
    """
    Tests set ids
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that ids was successfully created
    assert metrics_object.ids == {"an_id", "another_id"}


def test_mip_metrics_set_duplicate_reads(mip_metrics_deliverables_raw: dict):
    """
    Tests set duplicates read
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
    assert duplicate_read.id == expected_duplicate_read["id"]

    # THEN assert that value was set
    assert duplicate_read.value == float(expected_duplicate_read["value"]) * 100


def test_mip_metrics_set_mapped_reads(mip_metrics_deliverables_raw: dict):
    """
    Tests set mapped reads
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that mapped reads was set
    assert metrics_object.mapped_reads

    mapped_reads: MappedReads = metrics_object.mapped_reads.pop()

    # THEN assert that it was successfully created
    assert isinstance(mapped_reads, MappedReads)


def test_mip_metrics_set_mean_insert_size(mip_metrics_deliverables_raw: dict):
    """
    Tests set predicted sex
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that mean insert size was set
    assert metrics_object.mean_insert_size

    mean_insert_size: MeanInsertSize = metrics_object.mean_insert_size.pop()

    # THEN assert that it was successfully created
    assert isinstance(mean_insert_size, MeanInsertSize)


def test_mip_metrics_set_predicted_sex(mip_metrics_deliverables_raw: dict):
    """
    Tests set predicted sex
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that predicted sex was set
    assert metrics_object.predicted_sex

    predicted_sex: GenderCheck = metrics_object.predicted_sex.pop()

    # THEN assert that it was successfully created
    assert isinstance(predicted_sex, GenderCheck)


def test_instantiate_mip_metrics_set_id_metrics(mip_metrics_deliverables_raw: dict):
    """
    Tests set id metrics
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that id metrics was set
    assert metrics_object.id_metrics

    # WHEN looping through id metrics
    for id_metric in metrics_object.id_metrics:

        # THEN assert that id metrics was successfully created
        assert isinstance(id_metric, ParsedMetrics)

        # THEN assert that metrics are set for id
        if id_metric.id == "an_id":
            assert id_metric.duplicate_reads == 0.0748899652117993 * 100
            assert id_metric.mapped_reads == 0.9975489233589259 * 100
            assert id_metric.mean_insert_size == 422.0
            assert id_metric.predicted_sex == "female"


def test_get_id_metric(mip_metrics_deliverables_raw: dict):
    """
    Tests get id metrics
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # When getting an id_metric
    id_metric = get_id_metric(id="an_id", id_metrics=metrics_object.id_metrics)

    # THEN assert that id metric for id was returned
    assert id_metric.id == "an_id"
