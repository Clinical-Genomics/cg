"""Tests for delivery API"""

from pathlib import Path
from typing import List, Set

from cgmodels.cg.constants import Pipeline
from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.store.models import FamilySample, Sample, Family
from tests.store_helpers import StoreHelpers
from tests.store.conftest import fixture_case_obj
from tests.cli.deliver.conftest import fixture_fastq_delivery_bundle, fixture_mip_delivery_bundle


def test_get_delivery_path(
    base_store: Store, real_housekeeper_api: HousekeeperAPI, project_dir: Path, case_id: str
):
    """Test to create the delivery path."""
    # GIVEN a deliver api
    deliver_api = DeliverAPI(
        store=base_store,
        hk_api=real_housekeeper_api,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )
    customer_id = "cust000"
    ticket = "1234"
    deliver_api._set_customer_id(customer_id)
    deliver_api.set_ticket(ticket)

    # WHEN fetching the deliver path
    deliver_path = deliver_api.create_delivery_dir_path(case_name=case_id)

    # THEN assert that the path looks like expected
    assert deliver_path == Path(project_dir, customer_id, INBOX_NAME, ticket, case_id)


def test_get_case_analysis_files(populated_deliver_api: DeliverAPI, case_id: str):
    """Test to fetch case specific files for a case that exists in housekeeper."""
    deliver_api: DeliverAPI = populated_deliver_api
    # GIVEN a case which exist as bundle in hk with a version
    version_obj = deliver_api.hk_api.last_version(case_id)
    assert version_obj

    # GIVEN that a case object exists in the database
    link_objs: List[FamilySample] = deliver_api.store.family_samples(case_id)
    samples: List[Sample] = [link.sample for link in link_objs]
    sample_ids: Set[str] = set([sample.internal_id for sample in samples])

    # WHEN fetching all case files from the delivery api
    bundle_latest_files = deliver_api.get_case_files_from_version(
        version_obj=version_obj, sample_ids=sample_ids
    )

    # THEN housekeeper files should be returned
    assert bundle_latest_files


def test_get_case_files_from_version(
    analysis_store: Store,
    case_id: str,
    real_housekeeper_api: HousekeeperAPI,
    case_hk_bundle_no_files: dict,
    bed_file: Path,
    vcf_file: Path,
    project_dir: Path,
    helpers=StoreHelpers,
):
    # GIVEN a store with a case
    case_obj = analysis_store.family(case_id)
    assert case_obj.internal_id == case_id
    # GIVEN a delivery api
    deliver_api = DeliverAPI(
        store=analysis_store,
        hk_api=real_housekeeper_api,
        case_tags=[{"case-tag"}],
        sample_tags=[{"sample-tag"}],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )

    # GIVEN a housekeeper db populated with a bundle including a case specific file and a sample specific file
    case_hk_bundle_no_files["files"] = [
        {"path": bed_file.as_posix(), "archive": False, "tags": ["case-tag"]},
        {"path": str(vcf_file), "archive": False, "tags": ["sample-tag", "ADM1"]},
    ]
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=case_hk_bundle_no_files)

    # GIVEN a version object where two file exists
    version_obj: hk_models.Version = real_housekeeper_api.last_version(case_id)
    assert len(version_obj.files) == 2

    # GIVEN the sample ids of the samples
    link_objs: List[FamilySample] = analysis_store.family_samples(case_id)
    samples: List[Sample] = [link.sample for link in link_objs]
    sample_ids: Set[str] = set([sample.internal_id for sample in samples])

    # WHEN fetching the case files
    case_files = deliver_api.get_case_files_from_version(
        version_obj=version_obj, sample_ids=sample_ids
    )

    # THEN we should only get the case specific files back
    nr_files: int = 0
    case_file: Path
    for nr_files, case_file in enumerate(case_files, 1):
        assert case_file.name == bed_file.name
    # THEN assert that only the case-tag file was returned
    assert nr_files == 1


def test_get_sample_files_from_version(
    deliver_api: DeliverAPI,
    case_hk_bundle_no_files: dict,
    bed_file: Path,
    vcf_file: Path,
    project_dir: Path,
    case_id: str,
    helpers=StoreHelpers,
):
    """Test to fetch sample specific files from the deliver API.

    The purpose of the test is to see that only sample specific files are returned.
    """
    # GIVEN a case which exist as bundle in hk
    # GIVEN a housekeeper db populated with a bundle including a case specific file and a sample specific file
    hk_api = deliver_api.hk_api
    case_hk_bundle_no_files["files"] = [
        {"path": bed_file.as_posix(), "archive": False, "tags": ["case-tag"]},
        {"path": str(vcf_file), "archive": False, "tags": [AlignmentFileTag.CRAM, "ADM1"]},
    ]
    helpers.ensure_hk_bundle(hk_api, bundle_data=case_hk_bundle_no_files)
    # GIVEN a version object with some files
    version_obj: hk_models.Version = hk_api.last_version(case_id)
    assert len(version_obj.files) == 2

    # WHEN fetching the sample specific files
    sample_files = deliver_api.get_sample_files_from_version(
        version_obj=version_obj, sample_id="ADM1"
    )

    # THEN assert that only the sample specific file was returned
    nr_files: int = 0
    sample_file: Path
    for nr_files, sample_file in enumerate(sample_files, 1):
        assert sample_file.name == vcf_file.name
    # THEN assert that only the sample-tag file was returned
    assert nr_files == 1


def test_get_delivery_scope_case_only():
    """Testing the delivery scope of a case only delivery."""
    # GIVEN a case only delivery type
    delivery_type: Set[str] = {Pipeline.MIP_DNA}

    # WHEN getting the delivery scope
    sample_delivery, case_delivery = DeliverAPI.get_delivery_scope(delivery_type)

    # THEN a case_delivery should be True while sample_delivery False
    assert case_delivery
    assert not sample_delivery


def test_get_delivery_scope_sample_only():
    """Testing the delivery scope of a sample only delivery."""
    # GIVEN a sample only delivery type
    delivery_type = {Pipeline.FASTQ}

    # WHEN getting the delivery scope
    sample_delivery, case_delivery = DeliverAPI.get_delivery_scope(delivery_type)

    # THEN a sample_delivery should be True while case_delivery False
    assert not case_delivery
    assert sample_delivery


def test_get_delivery_scope_case_and_sample():
    """Testing the delivery scope of a case and sample delivery."""
    # GIVEN a case and sample delivery type
    delivery_type = {Pipeline.SARS_COV_2}

    # WHEN getting the delivery scope
    sample_delivery, case_delivery = DeliverAPI.get_delivery_scope(delivery_type)

    # THEN both case_delivery and sample_delivery should be True
    assert case_delivery
    assert sample_delivery


def test_deliver_files_enough_reads(
    caplog,
    case_id: str,
    deliver_api: DeliverAPI,
    deliver_api_destination_path: Path,
    fastq_delivery_bundle: dict,
    helpers: StoreHelpers,
    mip_delivery_bundle: dict,
    sample_id: str,
):
    """Tests the deliver_files method for a sample with enough reads."""
    # GIVEN a case to be delivered and a sample with enough reads
    case: Family = deliver_api.store.family(internal_id=case_id)
    sample: Sample = deliver_api.store.sample(sample_id)
    helpers.ensure_hk_bundle(deliver_api.hk_api, fastq_delivery_bundle, include=True)
    helpers.ensure_hk_bundle(deliver_api.hk_api, mip_delivery_bundle, include=True)

    # WHEN delivering files for the case
    deliver_api.deliver_files(case_obj=case)

    # THEN the sample folder should be created
    assert Path(deliver_api.project_base_path, deliver_api_destination_path, sample.name).exists()


def test_deliver_files_not_enough_reads(
    caplog,
    case_id: str,
    deliver_api: DeliverAPI,
    deliver_api_destination_path: Path,
    fastq_delivery_bundle: dict,
    helpers: StoreHelpers,
    mip_delivery_bundle: dict,
    sample_id: str,
):
    """Tests the deliver_files method for a sample with too few reads."""
    # GIVEN a case to be delivered and a sample with too few reads
    case: Family = deliver_api.store.family(internal_id=case_id)
    sample: Sample = deliver_api.store.sample(sample_id)
    sample.reads = 1
    helpers.ensure_hk_bundle(deliver_api.hk_api, fastq_delivery_bundle, include=True)
    helpers.ensure_hk_bundle(deliver_api.hk_api, mip_delivery_bundle, include=True)

    # WHEN delivering files for the case
    deliver_api.deliver_files(case_obj=case)

    # THEN the sample folder should not be created
    assert not Path(
        deliver_api.project_base_path, deliver_api_destination_path, sample.name
    ).exists()


def test_deliver_files_not_enough_reads_force(
    caplog,
    case_id: str,
    deliver_api: DeliverAPI,
    deliver_api_destination_path: Path,
    fastq_delivery_bundle: dict,
    helpers: StoreHelpers,
    mip_delivery_bundle: dict,
    sample_id: str,
):
    """Tests the deliver_files method for a sample with too few reads but with override."""
    # GIVEN a case to be delivered and a sample with too few reads
    case: Family = deliver_api.store.family(internal_id=case_id)
    sample: Sample = deliver_api.store.sample(sample_id)
    sample.reads = 1
    helpers.ensure_hk_bundle(deliver_api.hk_api, fastq_delivery_bundle, include=True)
    helpers.ensure_hk_bundle(deliver_api.hk_api, mip_delivery_bundle, include=True)

    # Given that the API was created with force_all=True
    deliver_api.deliver_failed_samples = True

    # WHEN delivering files for the case
    deliver_api.deliver_files(
        case_obj=case,
    )

    # THEN the sample folder should be created
    assert Path(deliver_api.project_base_path, deliver_api_destination_path, sample.name).exists()
