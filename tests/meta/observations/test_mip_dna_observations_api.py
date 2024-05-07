"""Test MIP-DNA observations API."""

import logging

from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case, Customer


def test_mip_dna_observations_upload(
    case_id: str,
    loqusdb_id: str,
    mip_dna_customer: Customer,
    number_of_loaded_variants: int,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test upload of observations."""
    caplog.set_level(logging.INFO)

    # GIVEN an observations API, a list of observation input files, and a workflow customer

    # GIVEN a case eligible for Loqusdb uploads
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    case.customer.internal_id = mip_dna_customer.internal_id

    # GIVEN a mock scenario for a successful upload
    mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS)
    mocker.patch.object(
        ObservationsAPI,
        "get_observations_input_files",
        return_value=mip_dna_observations_input_files,
    )
    mocker.patch.object(ObservationsAPI, "is_duplicate", return_value=False)
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN uploading the case observations to Loqusdb
    mip_dna_observations_api.upload(case)

    # THEN the case should be successfully uploaded
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


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
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
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
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#     case.links[0].sample.is_tumour = True
#
#     # WHEN getting the Loqusdb API
#     with pytest.raises(LoqusdbUploadCaseError):
#         # THEN an upload error should be raised and the execution aborted
#         mip_dna_observations_api.load_observations(case, observations_input_files)
#
#     assert f"Case {case.internal_id} has tumour samples. Cancelling upload." in caplog.text
#
#
# def test_mip_dna_delete_case(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     caplog: LogCaptureFixture,
# ):
#     """Test delete case from Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a Loqusdb instance filled with a case
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#
#     # WHEN deleting a case
#     mip_dna_observations_api.delete_case(case)
#
#     # THEN the case should be deleted from Loqusdb
#     assert f"Removed observations for case {case.internal_id} from Loqusdb" in caplog.text
#
#
# def test_mip_dna_delete_case_not_found(
#     helpers: StoreHelpers,
#     loqusdb_api: LoqusdbAPI,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     caplog: LogCaptureFixture,
# ):
#     """Test delete case from Loqusdb that has not been uploaded."""
#
#     # GIVEN an observations instance and a case that has not been uploaded to Loqusdb
#     loqusdb_api.process.stdout = None
#     mip_dna_observations_api.loqusdb_api = loqusdb_api
#     case: Case = helpers.add_case(mip_dna_observations_api.store)
#
#     # WHEN deleting a rare disease case that does not exist in Loqusdb
#     with pytest.raises(CaseNotFoundError):
#         # THEN a CaseNotFoundError should be raised
#         mip_dna_observations_api.delete_case(case)
#
#     assert (
#         f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
#         in caplog.text
#     )
#
#
