"""Test delivery API methods."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery
from cg.constants.delivery import INBOX_NAME
from cg.meta.delivery.delivery import DeliveryAPI
from cg.models.cg_config import CGConfig
from cg.models.delivery.delivery import DeliveryFile
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_is_sample_deliverable(delivery_context_microsalt: CGConfig, sample_id: str):
    """Test that a sample is deliverable."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a sample id with enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample)

    # THEN the sample should be deliverable
    assert is_deliverable


def test_is_sample_deliverable_false(
    delivery_context_microsalt: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a sample is not deliverable."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a sample without enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id_not_enough_reads)

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample)

    # THEN the sample should not be deliverable
    assert not is_deliverable


def test_is_sample_deliverable_force(
    delivery_context_microsalt: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a non-deliverable sample is deliverable with a force flag."""
    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a rare disease sample without enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id_not_enough_reads)

    # WHEN evaluating if sample is deliverable with a force flag
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample=sample, force=True)

    # THEN the sample should be deliverable
    assert is_deliverable


def test_convert_case_files_to_delivery_files(delivery_context_balsamic: CGConfig, case_id: str):
    """Test Housekeeper case files conversion to delivery files."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    housekeeper_api: HousekeeperAPI = delivery_context_balsamic.housekeeper_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object and list of Housekeeper files to be delivered
    case: Case = status_db.get_case_by_internal_id(case_id)
    hk_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[case_id]).all()

    # WHEN converting Housekeeper case files to delivery files
    delivery_files: list[DeliveryFile] = delivery_api.convert_files_to_delivery_files(
        files=hk_files, case=case, internal_id=case.internal_id, external_id=case.name
    )

    # THEN the delivery files should be correctly formatted
    hk_file: File = hk_files[0]
    delivery_file: DeliveryFile = delivery_files[0]
    destination_dir = Path(
        delivery_api.delivery_path,
        case.customer.internal_id,
        INBOX_NAME,
        case.latest_ticket,
        case.name,
    )
    assert delivery_file.source_path.as_posix() == hk_file.full_path
    assert delivery_file.destination_path.parent == destination_dir
    assert case.name in delivery_file.destination_path.as_posix()
    assert case.internal_id not in delivery_file.destination_path.as_posix()


def test_convert_sample_files_to_delivery_files(
    delivery_context_balsamic: CGConfig, case_id: str, sample_id: str
):
    """Test Housekeeper sample files conversion to delivery files."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    housekeeper_api: HousekeeperAPI = delivery_context_balsamic.housekeeper_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case, a sample object, and a list of sample Housekeeper files to be delivered
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)
    hk_sample_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[sample_id]).all()

    # WHEN converting Housekeeper sample files to delivery files
    delivery_files: list[DeliveryFile] = delivery_api.convert_files_to_delivery_files(
        files=hk_sample_files,
        case=case,
        internal_id=sample.internal_id,
        external_id=sample.name,
        analysis_sample_files=True,
    )

    # THEN the delivery sample files should be correctly formatted
    hk_file: File = hk_sample_files[0]
    delivery_file: DeliveryFile = delivery_files[0]
    destination_dir = Path(
        delivery_api.delivery_path,
        case.customer.internal_id,
        INBOX_NAME,
        case.latest_ticket,
        case.name,
        sample.name,
    )
    assert delivery_file.source_path.as_posix() == hk_file.full_path
    assert delivery_file.destination_path.parent == destination_dir
    assert sample.name in delivery_file.destination_path.as_posix()
    assert sample.internal_id not in delivery_file.destination_path.as_posix()


def test_convert_sample_files_to_delivery_files_with_case_id(
    delivery_context_balsamic: CGConfig, case_id: str, sample_id: str
):
    """
    Test Housekeeper sample files conversion to delivery files when sample files have case ID in
    their name.
    """

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    housekeeper_api: HousekeeperAPI = delivery_context_balsamic.housekeeper_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case, a sample object, and a list of sample Housekeeper files with case ID in their
    # name to be delivered
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)
    hk_sample_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[sample_id]).all()
    hk_case_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[case_id]).all()
    hk_files: list[File] = hk_sample_files + hk_case_files

    # WHEN converting Housekeeper sample files to delivery files
    delivery_files: list[DeliveryFile] = delivery_api.convert_files_to_delivery_files(
        files=hk_files,
        case=case,
        internal_id=sample.internal_id,
        external_id=sample.name,
        analysis_sample_files=True,
    )

    print(delivery_files)

    # THEN the delivery sample files should be correctly formatted and not contain case or sample
    # internal IDs
    for delivery_file in delivery_files:
        assert sample.name in delivery_file.destination_path.as_posix()
        assert sample.internal_id not in delivery_file.destination_path.as_posix()
        assert case.internal_id not in delivery_file.destination_path.as_posix()


def test_get_fastq_delivery_files_by_sample(
    delivery_context_microsalt: CGConfig,
    case_id: str,
    sample_id: str,
    delivery_fastq_file: Path,
    delivery_spring_file: Path,
):
    """Test get FASTQ delivery files for a sample."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN case and sample objects
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)

    # WHEN retrieving FASTQ delivery files by sample
    delivery_files: list[DeliveryFile] = delivery_api.get_fastq_delivery_files_by_sample(
        case=case, sample=sample
    )

    # THEN only FASTQ files should be returned
    assert isinstance(delivery_files[0], DeliveryFile)
    assert delivery_files[0].source_path.name == delivery_fastq_file.name
    for delivery_file in delivery_files:
        assert delivery_file.source_path.name != delivery_spring_file.name


def test_get_fastq_delivery_files_by_sample_not_deliverable(
    delivery_context_microsalt: CGConfig,
    case_id: str,
    sample_id_not_enough_reads: str,
    caplog: LogCaptureFixture,
):
    """Test get FASTQ delivery files for a sample that is not deliverable."""
    caplog.set_level(logging.INFO)

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN case and sample objects
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id_not_enough_reads)

    # WHEN retrieving FASTQ delivery files by a sample that is not deliverable
    delivery_files: list[DeliveryFile] = delivery_api.get_fastq_delivery_files_by_sample(
        case=case, sample=sample
    )

    # THEN no delivery files should be returned
    assert not delivery_files
    assert f"Sample {sample_id_not_enough_reads} is not deliverable" in caplog.text


def test_get_fastq_delivery_files(
    delivery_context_microsalt: CGConfig,
    case_id: str,
    delivery_fastq_file: Path,
    delivery_another_fastq_file: Path,
):
    """Test get FASTQ delivery files for all samples linked to a case."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a case object
    case: Case = status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving the FASTQ file to deliver
    delivery_files: list[DeliveryFile] = delivery_api.get_fastq_delivery_files(case=case)

    # THEN all the FASTQ sample files should be returned
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name in [
            delivery_fastq_file.name,
            delivery_another_fastq_file.name,
        ]


def test_get_analysis_sample_delivery_files_by_sample(
    delivery_context_balsamic: CGConfig, case_id: str, sample_id: str, delivery_cram_file: Path
):
    """Test get analysis files to deliver by sample."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN case and sample analysis objects
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)

    # WHEN retrieving delivery files by sample
    delivery_files: list[DeliveryFile] = delivery_api.get_analysis_sample_delivery_files_by_sample(
        case=case, sample=sample
    )

    # THEN the analysis cram file should be returned as a delivery file model
    assert isinstance(delivery_files[0], DeliveryFile)
    assert delivery_files[0].source_path.name == delivery_cram_file.name


def test_get_analysis_sample_delivery_files(
    delivery_context_balsamic: CGConfig,
    case_id: str,
    delivery_cram_file: Path,
    delivery_another_cram_file: Path,
):
    """Test get complete list of analysis sample files."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object
    case: Case = status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving sample delivery files
    delivery_files: list[DeliveryFile] = delivery_api.get_analysis_sample_delivery_files(case=case)

    # THEN the analysis cram files should be returned for all case samples
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name in [
            delivery_cram_file.name,
            delivery_another_cram_file.name,
        ]


def test_get_analysis_case_delivery_files(
    delivery_context_balsamic: CGConfig,
    case_id: str,
    delivery_report_file: Path,
    delivery_cram_file: Path,
    delivery_another_cram_file: Path,
):
    """Test analysis case delivery files retrieval."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object
    case: Case = status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving case delivery files
    delivery_files: list[DeliveryFile] = delivery_api.get_analysis_case_delivery_files(case=case)

    # THEN only case specific files should be returned, ignoring sample analysis files
    assert delivery_files[0].source_path.name == delivery_report_file.name
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name not in [
            delivery_cram_file.name,
            delivery_another_cram_file.name,
        ]


def test_get_delivery_files_fastq_delivery(
    delivery_context_microsalt: CGConfig,
    case_id: str,
    delivery_fastq_file: Path,
    delivery_another_fastq_file: Path,
):
    """Test get delivery files for FASTQ data delivery."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a case object with FASTQ data as delivery
    case: Case = status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving the FASTQ delivery files
    delivery_files: list[DeliveryFile] = delivery_api.get_delivery_files(case=case)

    # THEN only the FASTQ sample files should be returned
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name in [
            delivery_fastq_file.name,
            delivery_another_fastq_file.name,
        ]


def test_get_delivery_files_analysis_delivery(
    delivery_context_balsamic: CGConfig,
    case_id: str,
    delivery_report_file: Path,
    delivery_cram_file: Path,
    delivery_another_cram_file: Path,
):
    """Test get delivery files for analysis data delivery."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object with analysis files as data delivery
    case: Case = status_db.get_case_by_internal_id(case_id)
    case.data_delivery = DataDelivery.ANALYSIS_FILES

    # WHEN retrieving the analysis delivery files
    delivery_files: list[DeliveryFile] = delivery_api.get_delivery_files(case=case)

    # THEN only the analysis case and sample files should be returned
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name in [
            delivery_report_file.name,
            delivery_cram_file.name,
            delivery_another_cram_file.name,
        ]


def test_get_delivery_files_fastq_analysis_delivery(
    delivery_context_balsamic: CGConfig,
    case_id: str,
    delivery_report_file: Path,
    delivery_cram_file: Path,
    delivery_another_cram_file: Path,
    delivery_fastq_file: Path,
    delivery_another_fastq_file: Path,
):
    """Test get delivery files for FASTQ analysis data delivery."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object with FASTQ analysis as data delivery
    case: Case = status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving the FASTQ analysis delivery files
    delivery_files: list[DeliveryFile] = delivery_api.get_delivery_files(case=case)

    # THEN analysis case and sample files should be returned together with the fastqs
    for delivery_file in delivery_files:
        assert isinstance(delivery_file, DeliveryFile)
        assert delivery_file.source_path.name in [
            delivery_report_file.name,
            delivery_cram_file.name,
            delivery_another_cram_file.name,
            delivery_fastq_file.name,
            delivery_another_fastq_file.name,
        ]
