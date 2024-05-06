"""Test observations API methods."""

from pathlib import Path

from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CustomerId
from cg.constants.observations import LoqusdbInstance, MipDNALoadParameters
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case, Customer


def test_get_loqusdb_api(cg_context: CGConfig, mip_dna_observations_api: MipDNAObservationsAPI):
    """Test Loqusdb API retrieval given a Loqusdb instance."""

    # GIVEN a WES Loqusdb instance and an observations API
    loqusdb_instance = LoqusdbInstance.WES

    # GIVEN the expected Loqusdb config dictionary
    loqusdb_wes_config: dict[str, Path] = cg_context.loqusdb_wes

    # WHEN calling the Loqusdb API get method
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(loqusdb_instance)

    # THEN a WES Loqusdb API should be returned
    assert isinstance(loqusdb_api, LoqusdbAPI)
    assert loqusdb_api.binary_path == loqusdb_wes_config.binary_path
    assert loqusdb_api.config_path == loqusdb_wes_config.config_path


def test_is_duplicate(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that is not in Loqusdb."""

    # GIVEN a Loqusdb instance with no case duplicates
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN there should be no duplicates in Loqusdb
    assert is_duplicate is False


def test_is_duplicate_true(
    case_id: str,
    loqusdb_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value={"case_id": case_id})

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN an upload of a duplicate case should be detected
    assert is_duplicate is True


def test_is_duplicate_loqusdb_id(
    case_id: str,
    loqusdb_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    case.links[0].sample.loqusdb_id = loqusdb_id
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that the sample observations have already been uploaded
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN a duplicated upload should be identified
    assert is_duplicate is True


def test_is_customer_eligible_for_observations_upload(
    mip_dna_customer: Customer, mip_dna_observations_api: MipDNAObservationsAPI
):
    """Test if customer is eligible for observations upload."""

    # GIVEN a MIP-DNA customer and observations API
    customer_id: str = mip_dna_customer.internal_id

    # WHEN verifying if the customer is eligible for Balsamic observations upload
    is_customer_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_customer_eligible_for_observations_upload(customer_id)
    )

    # THEN the customer's data should be eligible for uploads
    assert is_customer_eligible_for_observations_upload


def test_is_customer_eligible_for_observations_upload_false(
    mip_dna_observations_api: MipDNAObservationsAPI, caplog: LogCaptureFixture
):
    """Test if customer is not eligible for observations upload."""

    # GIVEN a CG internal customer ID and observations API
    customer_id: str = CustomerId.CG_INTERNAL_CUSTOMER

    # WHEN verifying if the customer is eligible for Balsamic observations upload
    is_customer_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_customer_eligible_for_observations_upload(customer_id)
    )

    # THEN the customer's data should not be eligible for uploads
    assert not is_customer_eligible_for_observations_upload
    assert f"Customer {customer_id} is not whitelisted for Loqusdb uploads" in caplog.text


def test_is_sequencing_method_eligible_for_observations_upload(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mocker: MockFixture,
):
    """Test if the sequencing method is eligible for observations uploads."""

    # GIVEN a MIP-DNA case ID and an observations API

    # GIVEN a supported data analysis type
    sequencing_method = SequencingMethod.WGS
    mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=sequencing_method)

    # WHEN verifying that the sequencing method is eligible for observations uploads
    is_sequencing_method_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sequencing_method_eligible_for_observations_upload(case_id)
    )

    # THEN the sequencing method should be eligible for observations uploads
    assert is_sequencing_method_eligible_for_observations_upload


def test_is_sequencing_method_eligible_for_observations_upload_false(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the sequencing method is eligible for observations uploads."""

    # GIVEN a MIP-DNA case ID and an observations API

    # GIVEN a non-supported data analysis type
    sequencing_method = SequencingMethod.WTS
    mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=sequencing_method)

    # WHEN verifying that the sequencing method is eligible for observations uploads
    is_sequencing_method_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sequencing_method_eligible_for_observations_upload(case_id)
    )

    # THEN the sequencing method should not be eligible for observations uploads
    assert not is_sequencing_method_eligible_for_observations_upload
    assert (
        f"Sequencing method {sequencing_method} is not supported by Loqusdb uploads" in caplog.text
    )
