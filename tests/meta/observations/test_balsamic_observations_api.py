"""Test Balsamic observations API."""

import logging

from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import Case, Customer


def test_balsamic_observations_upload(
    case_id: str,
    loqusdb_id: str,
    balsamic_customer: Customer,
    number_of_loaded_variants: int,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test upload of observations."""
    caplog.set_level(logging.INFO)

    # GIVEN an observations API, a list of observation input files, and a workflow customer

    # GIVEN a case eligible for Loqusdb uploads
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    case.customer.internal_id = balsamic_customer.internal_id
    case.samples[0].is_tumour = True

    # GIVEN a mock scenario for a successful upload
    mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS)
    mocker.patch.object(
        ObservationsAPI,
        "get_observations_input_files",
        return_value=balsamic_observations_input_files,
    )
    mocker.patch.object(ObservationsAPI, "is_duplicate", return_value=False)
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )

    # WHEN uploading the case observations to Loqusdb
    balsamic_observations_api.upload(case)

    # THEN the case should be successfully uploaded
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_is_analysis_type_eligible_for_observations_upload(
    case_id: str, balsamic_observations_api: BalsamicObservationsAPI, mocker: MockFixture
):
    """Test if the analysis type is eligible for observation uploads."""

    # GIVEN a case ID and a Balsamic observations API

    # GIVEN a case with tumor samples
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case_id)
    )

    # THEN the analysis type should be eligible for observation uploads
    assert is_analysis_type_eligible_for_observations_upload


def test_is_analysis_type_eligible_for_observations_upload_false(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the analysis type is not eligible for observation uploads."""

    # GIVEN a case ID and a Balsamic observations API

    # GIVEN a case without tumor samples (normal-only analysis)
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=True)

    # WHEN checking analysis type eligibility for a case
    is_analysis_type_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_analysis_type_eligible_for_observations_upload(case_id)
    )

    # THEN the analysis type should not be eligible for observation uploads
    assert not is_analysis_type_eligible_for_observations_upload
    assert f"Normal only analysis {case_id} is not supported for Loqusdb uploads" in caplog.text


# def test_balsamic_load_observations(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     balsamic_observations_input_files: BalsamicObservationsInputFiles,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
#     mocker,
# ):
#     """Test loading of cancer case observations."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mock BALSAMIC observations API and a list of observations input files
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(balsamic_observations_api, "is_duplicate", return_value=False)
#
#     # WHEN loading the case to Loqusdb
#     balsamic_observations_api.load_observations(case, balsamic_observations_input_files)
#
#     # THEN the observations should be loaded successfully
#     assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
#
#
# def test_balsamic_load_observations_duplicate(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     caplog: LogCaptureFixture,
#     mocker,
# ):
#     """Test upload cancer duplicate case observations to Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a balsamic observations API and a case object that has already been uploaded to Loqusdb
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
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
# def test_balsamic_load_cancer_observations(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     balsamic_observations_input_files: BalsamicObservationsInputFiles,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
# ):
#     """Test loading of case observations for cancer."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mock BALSAMIC observations API and a list of observations input files
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#
#     # WHEN loading the case to a somatic Loqusdb instance
#     balsamic_observations_api.load_cancer_observations(
#         case, balsamic_observations_input_files, balsamic_observations_api.loqusdb_somatic_api
#     )
#
#     # THEN the observations should be loaded successfully
#     assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
#     print(caplog.text)
#
#
# def test_balsamic_delete_case(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     caplog: LogCaptureFixture,
# ):
#     """Test delete balsamic case observations from Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a Loqusdb instance and a case that has been uploaded to both somatic and tumor instances
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#
#     # WHEN deleting the case
#     balsamic_observations_api.delete_case(case)
#
#     # THEN the case should be deleted from Loqusdb
#     assert f"Removed observations for case {case.internal_id} from Loqusdb" in caplog.text
#
#
# def test_balsamic_delete_case_not_found(
#     helpers: StoreHelpers,
#     loqusdb_api: LoqusdbAPI,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     caplog: LogCaptureFixture,
# ):
#     """Test delete balsamic case observations from Loqusdb that have not been uploaded."""
#
#     # GIVEN empty Loqusdb instances
#     loqusdb_api.process.stdout = None
#     balsamic_observations_api.loqusdb_somatic_api = loqusdb_api
#     balsamic_observations_api.loqusdb_tumor_api = loqusdb_api
#     case: Case = helpers.add_case(balsamic_observations_api.store)
#
#     # WHEN deleting a cancer case that does not exist in Loqusdb
#     with pytest.raises(CaseNotFoundError):
#         # THEN a CaseNotFoundError should be raised
#         balsamic_observations_api.delete_case(case)
#
#     assert (
#         f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
#         in caplog.text
#     )
