"""Test delivery API methods."""

from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.meta.delivery.delivery import DeliveryAPI
from cg.models.cg_config import CGConfig
from cg.models.delivery.delivery import DeliveryFile
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_convert_case_files_to_delivery_files(delivery_context_balsamic: CGConfig, case_id: str):
    """Test Housekeeper case files conversion to delivery files."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_balsamic.delivery_api
    housekeeper_api: HousekeeperAPI = delivery_context_balsamic.housekeeper_api
    status_db: Store = delivery_context_balsamic.status_db

    # GIVEN a case object and list of HK files to be delivered
    case: Case = status_db.get_case_by_internal_id(case_id)
    hk_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[case_id]).all()

    # WHEN making the case files conversion
    delivery_files: list[DeliveryFile] = delivery_api.convert_files_to_delivery_files(
        files=hk_files, case=case, source_id=case.internal_id, destination_id=case.name
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

    # GIVEN a case, a sample object, and list of sample HK files to be delivered
    case: Case = status_db.get_case_by_internal_id(case_id)
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)
    hk_sample_files: list[File] = housekeeper_api.get_files(bundle=case_id, tags=[sample_id]).all()

    # WHEN making the sample files conversion
    delivery_files: list[DeliveryFile] = delivery_api.convert_files_to_delivery_files(
        files=hk_sample_files,
        case=case,
        source_id=sample.internal_id,
        destination_id=sample.name,
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
