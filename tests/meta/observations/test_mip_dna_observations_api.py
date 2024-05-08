"""Test MIP-DNA observations API."""

from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.store.models import Case, Customer


def test_is_sample_type_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI
):
    """Test if the sample type is eligible for observation uploads."""

    # GIVEN a case without tumor samples and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_sample_type_eligible_for_observations_upload


def test_is_sample_type_not_eligible_for_observations_upload(
    case_id: str, mip_dna_observations_api: MipDNAObservationsAPI
):
    """Test if the sample type is not eligible for observation uploads."""

    # GIVEN a case with tumor samples and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
    case.samples[0].is_tumour = True

    # WHEN checking sample type eligibility for a case
    is_sample_type_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_sample_type_eligible_for_observations_upload(case)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_sample_type_eligible_for_observations_upload


def test_is_case_eligible_for_observations_upload(
    case_id: str,
    mip_dna_customer: Customer,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mocker: MockFixture,
):
    """Test whether a case is eligible for MIP-DNA observation uploads."""

    # GIVEN a case and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a MIP-DNA customer and a scenario for Loqusdb uploads
    case.customer.internal_id = mip_dna_customer.internal_id
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS
    )
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should be eligible for observation uploads
    assert is_case_eligible_for_observations_upload


def test_is_case_not_eligible_for_observations_upload(
    case_id: str,
    mip_dna_customer: Customer,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mocker: MockFixture,
):
    """Test whether a case is not eligible for MIP-DNA observation uploads."""

    # GIVEN a case and a MIP-DNA observations API
    case: Case = mip_dna_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a MIP-DNA customer and a scenario for Loqusdb uploads with an invalid sequencing method
    case.customer.internal_id = mip_dna_customer.internal_id
    mocker.patch.object(
        MipDNAAnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WTS
    )
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        mip_dna_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should not be eligible for observation uploads
    assert not is_case_eligible_for_observations_upload


# def test_mip_dna_load_observations(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
#     mocker,
# ):
#     """Test loading of case observations for rare disease."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mock MIP DNA observations API and a list of observations input files
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#
#     # WHEN loading the case to Loqusdb
#     mip_dna_observations_api.load_observations(case, observations_input_files)
#
#     # THEN the observations should be loaded without any errors
#     assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
#
#
# def test_mip_dna_load_observations_duplicate(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     caplog: LogCaptureFixture,
#     mocker,
# ):
#     """Test upload case duplicate to Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mocked observations API and a case object that has already been uploaded to Loqusdb
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=True)
#
#     # WHEN uploading the case observations to Loqusdb
#     with pytest.raises(LoqusdbDuplicateRecordError):
#         # THEN a duplicate record error should be raised
#         mip_dna_observations_api.load_observations(case, observations_input_files)
#
#     assert f"Case {case.internal_id} has already been uploaded to Loqusdb" in caplog.text
#
#
# def test_mip_dna_load_observations_tumor_case(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     caplog: LogCaptureFixture,
#     mocker,
# ):
#     """Test loading of a tumor case to Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a MIP DNA observations API and a case object with a tumour sample
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#     case.links[0].sample.is_tumour = True
#
#     # WHEN getting the Loqusdb API
#     with pytest.raises(LoqusdbUploadCaseError):
#         # THEN an upload error should be raised and the execution aborted
#         mip_dna_observations_api.load_observations(case, observations_input_files)
#
#     assert f"Case {case.internal_id} has tumour samples. Cancelling upload." in caplog.text
