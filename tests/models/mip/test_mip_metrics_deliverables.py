"""Test MIP metrics deliverables"""

from cg.models.mip.mip_metrics_deliverables import (
    MetricsDeliverables,
    DuplicateReads,
    ParsedMetrics,
    GenderCheck,
    MeanInsertSize,
    MappedReads,
    get_sample_id_metric,
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


def test_instantiate_mip_metrics_sample_ids(mip_metrics_deliverables_raw: dict):
    """
    Tests set sample_ids
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that sample_ids was successfully created
    assert metrics_object.sample_ids == {"an_id", "another_id"}


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
    assert duplicate_read.sample_id == expected_duplicate_read["id"]

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


def test_instantiate_mip_metrics_set_sample_id_metrics(mip_metrics_deliverables_raw: dict):
    """
    Tests set sample_id metrics
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # THEN assert that sample_id metrics was set
    assert metrics_object.sample_id_metrics

    # WHEN looping through sample_id metrics
    for sample_id_metric in metrics_object.sample_id_metrics:

        # THEN assert that sample_id metrics was successfully created
        assert isinstance(sample_id_metric, ParsedMetrics)

        # THEN assert that metrics are set for sample_id
        if sample_id_metric.sample_id == "an_id":
            assert sample_id_metric.duplicate_reads == 0.0748899652117993 * 100
            assert sample_id_metric.mapped_reads == 0.9975489233589259 * 100
            assert sample_id_metric.mean_insert_size == 422.0
            assert sample_id_metric.predicted_sex == "female"


def test_get_sample_id_metric(mip_metrics_deliverables_raw: dict):
    """
    Tests get sample_id metrics
    """
    # GIVEN a dictionary with the some metrics

    # WHEN instantiating a MetricsDeliverables object
    metrics_object = MetricsDeliverables(**mip_metrics_deliverables_raw)

    # When getting an sample_id_metric
    sample_id_metric = get_sample_id_metric(
        sample_id="an_id", sample_id_metrics=metrics_object.sample_id_metrics
    )

    # THEN assert that sample_id metric for sample_id was returned
    assert sample_id_metric.sample_id == "an_id"
