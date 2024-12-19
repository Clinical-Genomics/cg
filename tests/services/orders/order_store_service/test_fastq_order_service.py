from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.store.models import Application, Case, Sample
from cg.store.store import Store


def test_store_samples(
    base_store: Store,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
    fastq_order: FastqOrder,
):
    # GIVEN a basic store with no samples and a fastq order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN it should store the samples and create one raw-data case and one maf case
    assert len(new_samples) == 2
    assert len(base_store._get_query(table=Sample).all()) == 2
    assert base_store._get_query(table=Case).count() == 2
    sample_with_maf_case = new_samples[0]
    assert len(sample_with_maf_case.links) == 2
    family_link = sample_with_maf_case.links[0]
    assert family_link.case.data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]


def test_store_samples_sex_stored(
    base_store: Store,
    fastq_order: FastqOrder,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN the sample sex should be stored
    assert new_samples[0].sex == "male"


def test_store_fastq_samples_non_tumour_wgs_to_mip(
    base_store: Store, fastq_order: FastqOrder, store_fastq_order_service: StoreFastqOrderService
):
    # GIVEN a basic store with no samples and a non-tumour fastq order as wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    base_store.get_application_by_tag(fastq_order.samples[0].application).prep_category = (
        SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    )
    fastq_order.samples[0].tumour = False

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN the analysis for the case should be MAF
    assert new_samples[0].links[0].case.data_analysis == Workflow.MIP_DNA


def test_store_fastq_samples_tumour_wgs_to_fastq(
    base_store: Store,
    fastq_order: FastqOrder,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a tumour fastq order as wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    base_store.get_application_by_tag(fastq_order.samples[0].application).prep_category = (
        SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    )
    fastq_order.samples[1].tumour = True

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN the analysis for the case should be RAW_DATA
    assert new_samples[1].links[0].case.data_analysis == Workflow.RAW_DATA


def test_store_fastq_samples_non_wgs_as_fastq(
    base_store: Store,
    fastq_order: FastqOrder,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order as non wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    non_wgs_prep_category = SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING

    non_wgs_applications = base_store._get_query(table=Application).filter(
        Application.prep_category == non_wgs_prep_category
    )

    assert non_wgs_applications

    for sample in fastq_order.samples:
        sample.application = non_wgs_applications[0].tag

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN the analysis for the case should be RAW_DATA (none)
    assert new_samples[0].links[0].case.data_analysis == Workflow.RAW_DATA
