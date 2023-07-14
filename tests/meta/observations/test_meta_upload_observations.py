"""Test observations API methods."""

import logging
from typing import Dict

import pytest
from _pytest.logging import LogCaptureFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LoqusdbInstance, MipDNALoadParameters, LoqusdbMipCustomers
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbDuplicateRecordError, LoqusdbUploadCaseError, CaseNotFoundError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import (
    MipDNAObservationsInputFiles,
    BalsamicObservationsInputFiles,
)
from cg.store import Store
from cg.store.models import Family
from cg.store.models import Customer
from tests.store_helpers import StoreHelpers


def test_observations_upload(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    nr_of_loaded_variants: int,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test upload observations method."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mocked observations API and a list of mocked observations files
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    case.customer.internal_id = LoqusdbMipCustomers.KLINISK_IMMUNOLOGI.value
    mocker.patch.object(
        mip_dna_observations_api,
        "get_observations_input_files",
        return_value=observations_input_files,
    )
    mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)

    # WHEN uploading the case observations to Loqusdb
    mip_dna_observations_api.upload(case)

    # THEN the case should be successfully uploaded
    assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_get_loqusdb_api(
    mip_dna_observations_api: MipDNAObservationsAPI,
    loqusdb_config_dict: Dict[LoqusdbInstance, dict],
):
    """Test Loqusdb API retrieval given a Loqusdb instance."""

    # GIVEN the expected Loqusdb config dictionary

    # GIVEN a WES Loqusdb instance and an observations API
    loqusdb_instance = LoqusdbInstance.WES

    # WHEN calling the Loqusdb API get method
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(loqusdb_instance)

    # THEN a WES loqusdb api should be returned
    assert isinstance(loqusdb_api, LoqusdbAPI)
    assert loqusdb_api.binary_path == loqusdb_config_dict[LoqusdbInstance.WES]["binary_path"]
    assert loqusdb_api.config_path == loqusdb_config_dict[LoqusdbInstance.WES]["config_path"]


def test_is_duplicate(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    analysis_store: Store,
    mocker,
):
    """Test duplicate extraction for a case that is not in Loqusdb."""

    # GIVEN a Loqusdb instance with no case duplicates
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_case", return_value=None)
    mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_duplicate", return_value=False)

    # WHEN checking that a case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=mip_dna_observations_api.loqusdb_api,
        profile_vcf_path=observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN there should be no duplicates in Loqusdb
    assert is_duplicate is False


def test_is_duplicate_case_output(
    case_id: str,
    observations_input_files: MipDNAObservationsInputFiles,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)

    # WHEN checking that a case has already been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=mip_dna_observations_api.loqusdb_api,
        profile_vcf_path=observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN an upload of a duplicate case should be detected
    assert is_duplicate is True


def test_is_duplicate_loqusdb_id(
    case_id: str,
    loqusdb_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    analysis_store: Store,
    mocker,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    case.links[0].sample.loqusdb_id = loqusdb_id
    mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_case", return_value=None)
    mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_duplicate", return_value=False)

    # WHEN checking that the sample observations have already been uploaded
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=mip_dna_observations_api.loqusdb_api,
        profile_vcf_path=observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN a duplicated upload should be identified
    assert is_duplicate is True


def test_check_customer_loqusdb_permissions(
    customer_rare_diseases: Customer,
    customer_balsamic: Customer,
    mip_dna_observations_api: MipDNAObservationsAPI,
    caplog: LogCaptureFixture,
):
    """Test customers Loqusdb permissions."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a MIP observations API, a Rare Disease customer and a Cancer customer

    # WHEN verifying the permissions for Loqusdb upload
    mip_dna_observations_api.check_customer_loqusdb_permissions(customer_rare_diseases)

    # THEN it should be only possible to upload data from a RD customer
    assert f"Valid customer {customer_rare_diseases.internal_id} for Loqusdb uploads" in caplog.text
    with pytest.raises(LoqusdbUploadCaseError):
        mip_dna_observations_api.check_customer_loqusdb_permissions(customer_balsamic)


def test_mip_dna_get_loqusdb_instance(mip_dna_observations_api: MipDNAObservationsAPI):
    """Test Loqusdb instance retrieval given a sequencing method."""

    # GIVEN a rare disease observations API with a WES as sequencing method
    mip_dna_observations_api.sequencing_method = SequencingMethod.WES

    # WHEN getting the Loqusdb instance
    loqusdb_instance = mip_dna_observations_api.get_loqusdb_instance()

    # THEN the correct loqusdb instance should be returned
    assert loqusdb_instance == LoqusdbInstance.WES


def test_mip_dna_get_loqusdb_instance_not_supported(
    mip_dna_observations_api: MipDNAObservationsAPI, caplog: LogCaptureFixture
):
    """Test Loqusdb instance retrieval given a not supported sequencing method."""

    # GIVEN a rare disease observations API with a WTS sequencing method
    mip_dna_observations_api.sequencing_method = SequencingMethod.WTS

    # WHEN getting the Loqusdb instance
    with pytest.raises(LoqusdbUploadCaseError):
        # THEN the upload should be canceled
        mip_dna_observations_api.get_loqusdb_instance()

    assert (
        f"Sequencing method {SequencingMethod.WTS} is not supported by Loqusdb. Cancelling upload."
        in caplog.text
    )


def test_mip_dna_load_observations(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    nr_of_loaded_variants: int,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test loading of case observations for rare disease."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mock MIP DNA observations API and a list of observations input files
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)

    # WHEN loading the case to Loqusdb
    mip_dna_observations_api.load_observations(case, observations_input_files)

    # THEN the observations should be loaded without any errors
    assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_mip_dna_load_observations_duplicate(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test upload case duplicate to Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mocked observations API and a case object that has already been uploaded to Loqusdb
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=True)

    # WHEN uploading the case observations to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        # THEN a duplicate record error should be raised
        mip_dna_observations_api.load_observations(case, observations_input_files)

    assert f"Case {case.internal_id} has already been uploaded to Loqusdb" in caplog.text


def test_mip_dna_load_observations_tumor_case(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test loading of a tumor case to Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a MIP DNA observations API and a case object with a tumour sample
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
    case.links[0].sample.is_tumour = True

    # WHEN getting the Loqusdb API
    with pytest.raises(LoqusdbUploadCaseError):
        # THEN an upload error should be raised and the execution aborted
        mip_dna_observations_api.load_observations(case, observations_input_files)

    assert f"Case {case.internal_id} has tumour samples. Cancelling upload." in caplog.text


def test_mip_dna_delete_case(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test delete case from Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb instance filled with a case
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)

    # WHEN deleting a case
    mip_dna_observations_api.delete_case(case)

    # THEN the case should be deleted from Loqusdb
    assert f"Removed observations for case {case.internal_id} from Loqusdb" in caplog.text


def test_mip_dna_delete_case_not_found(
    base_context: CGConfig,
    helpers: StoreHelpers,
    loqusdb_api: LoqusdbAPI,
    mip_dna_observations_api: MipDNAObservationsAPI,
    caplog: LogCaptureFixture,
):
    """Test delete case from Loqusdb that has not been uploaded."""
    store: Store = base_context.status_db

    # GIVEN an observations instance and a case that has not been uploaded to Loqusdb
    loqusdb_api.process.stdout = None
    mip_dna_observations_api.loqusdb_api = loqusdb_api
    case: Family = helpers.add_case(store)

    # WHEN deleting a rare disease case that does not exist in Loqusdb
    with pytest.raises(CaseNotFoundError):
        # THEN a CaseNotFoundError should be raised
        mip_dna_observations_api.delete_case(case)

    assert (
        f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
        in caplog.text
    )


def test_balsamic_load_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    nr_of_loaded_variants: int,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test loading of cancer case observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mock BALSAMIC observations API and a list of observations input files
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(balsamic_observations_api, "is_duplicate", return_value=False)

    # WHEN loading the case to Loqusdb
    balsamic_observations_api.load_observations(case, balsamic_observations_input_files)

    # THEN the observations should be loaded successfully
    assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_balsamic_load_observations_duplicate(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    observations_input_files: MipDNAObservationsInputFiles,
    analysis_store: Store,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test upload cancer duplicate case observations to Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a balsamic observations API and a case object that has already been uploaded to Loqusdb
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=True)

    # WHEN uploading the case observations to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        # THEN a duplicate record error should be raised
        mip_dna_observations_api.load_observations(case, observations_input_files)

    assert f"Case {case.internal_id} has already been uploaded to Loqusdb" in caplog.text


def test_balsamic_load_cancer_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    nr_of_loaded_variants: int,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test loading of case observations for cancer."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a mock BALSAMIC observations API and a list of observations input files
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)

    # WHEN loading the case to a somatic Loqusdb instance
    balsamic_observations_api.load_cancer_observations(
        case, balsamic_observations_input_files, balsamic_observations_api.loqusdb_somatic_api
    )

    # THEN the observations should be loaded successfully
    assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
    print(caplog.text)


def test_balsamic_delete_case(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    analysis_store: Store,
    caplog: LogCaptureFixture,
):
    """Test delete balsamic case observations from Loqusdb."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Loqusdb instance and a case that has been uploaded to both somatic and tumor instances
    case: Family = analysis_store.get_case_by_internal_id(internal_id=case_id)

    # WHEN deleting the case
    balsamic_observations_api.delete_case(case)

    # THEN the case should be deleted from Loqusdb
    assert f"Removed observations for case {case.internal_id} from Loqusdb" in caplog.text


def test_balsamic_delete_case_not_found(
    base_context: CGConfig,
    helpers: StoreHelpers,
    loqusdb_api: LoqusdbAPI,
    balsamic_observations_api: BalsamicObservationsAPI,
    caplog: LogCaptureFixture,
):
    """Test delete balsamic case observations from Loqusdb that have not been uploaded."""
    store: Store = base_context.status_db

    # GIVEN empty Loqusdb instances
    loqusdb_api.process.stdout = None
    balsamic_observations_api.loqusdb_somatic_api = loqusdb_api
    balsamic_observations_api.loqusdb_tumor_api = loqusdb_api
    case: Family = helpers.add_case(store)

    # WHEN deleting a cancer case that does not exist in Loqusdb
    with pytest.raises(CaseNotFoundError):
        # THEN a CaseNotFoundError should be raised
        balsamic_observations_api.delete_case(case)

    assert (
        f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
        in caplog.text
    )
