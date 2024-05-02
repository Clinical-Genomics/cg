# """Test observations API methods."""
#
# import logging
#
# import pytest
# from _pytest.logging import LogCaptureFixture
# from pytest_mock import MockFixture
#
# from cg.apps.loqus import LoqusdbAPI
# from cg.constants.observations import LoqusdbInstance, MipDNALoadParameters
# from cg.constants.sequencing import SequencingMethod
# from cg.exc import (
#     CaseNotFoundError,
#     LoqusdbDuplicateRecordError,
#     LoqusdbUploadCaseError,
# )
# from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
# from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
# from cg.meta.workflow.analysis import AnalysisAPI
# from cg.models.observations.input_files import (
#     BalsamicObservationsInputFiles,
#     MipDNAObservationsInputFiles,
# )
# from cg.store.models import Case, Customer
# from tests.store_helpers import StoreHelpers
#
#
# def test_observations_upload(
#     case_id: str,
#     customer_rare_diseases: Customer,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
#     mocker: MockFixture,
# ):
#     """Test upload observations method."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mocked observations API and a list of mocked observations files
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     case.customer.internal_id = customer_rare_diseases.internal_id
#     mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS)
#     mocker.patch.object(mip_dna_observations_api, "set_loqusdb_instance", return_value=None)
#     mocker.patch.object(
#         mip_dna_observations_api,
#         "get_observations_input_files",
#         return_value=observations_input_files,
#     )
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#
#     # WHEN uploading the case observations to Loqusdb
#     mip_dna_observations_api.upload(case)
#
#     # THEN the case should be successfully uploaded
#     assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
#
#
# def test_get_loqusdb_api(
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     loqusdb_config_dict: dict[LoqusdbInstance, dict],
# ):
#     """Test Loqusdb API retrieval given a Loqusdb instance."""
#
#     # GIVEN the expected Loqusdb config dictionary
#
#     # GIVEN a WES Loqusdb instance and an observations API
#     loqusdb_instance = LoqusdbInstance.WES
#
#     # WHEN calling the Loqusdb API get method
#     loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(loqusdb_instance)
#
#     # THEN a WES loqusdb api should be returned
#     assert isinstance(loqusdb_api, LoqusdbAPI)
#     assert loqusdb_api.binary_path == loqusdb_config_dict[LoqusdbInstance.WES]["binary_path"]
#     assert loqusdb_api.config_path == loqusdb_config_dict[LoqusdbInstance.WES]["config_path"]
#
#
# def test_is_duplicate(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     mocker: MockFixture,
# ):
#     """Test duplicate extraction for a case that is not in Loqusdb."""
#
#     # GIVEN a Loqusdb instance with no case duplicates
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
#     mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)
#
#     # WHEN checking that a case has not been uploaded to Loqusdb
#     is_duplicate: bool = mip_dna_observations_api.is_duplicate(
#         case=case,
#         loqusdb_api=mip_dna_observations_api.loqusdb_api,
#         profile_vcf_path=observations_input_files.profile_vcf_path,
#         profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
#     )
#
#     # THEN there should be no duplicates in Loqusdb
#     assert is_duplicate is False
#
#
# def test_is_duplicate_case_output(
#     case_id: str,
#     observations_input_files: MipDNAObservationsInputFiles,
#     mip_dna_observations_api: MipDNAObservationsAPI,
# ):
#     """Test duplicate extraction for a case that already exists in Loqusdb."""
#
#     # GIVEN a Loqusdb instance with a duplicated case
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#
#     # WHEN checking that a case has already been uploaded to Loqusdb
#     is_duplicate: bool = mip_dna_observations_api.is_duplicate(
#         case=case,
#         loqusdb_api=mip_dna_observations_api.loqusdb_api,
#         profile_vcf_path=observations_input_files.profile_vcf_path,
#         profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
#     )
#
#     # THEN an upload of a duplicate case should be detected
#     assert is_duplicate is True
#
#
# def test_is_duplicate_loqusdb_id(
#     case_id: str,
#     loqusdb_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     mocker: MockFixture,
# ):
#     """Test duplicate extraction for a case that already exists in Loqusdb."""
#
#     # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     case.links[0].sample.loqusdb_id = loqusdb_id
#     mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_case", return_value=None)
#     mocker.patch.object(mip_dna_observations_api.loqusdb_api, "get_duplicate", return_value=False)
#
#     # WHEN checking that the sample observations have already been uploaded
#     is_duplicate: bool = mip_dna_observations_api.is_duplicate(
#         case=case,
#         loqusdb_api=mip_dna_observations_api.loqusdb_api,
#         profile_vcf_path=observations_input_files.profile_vcf_path,
#         profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
#     )
#
#     # THEN a duplicated upload should be identified
#     assert is_duplicate is True
#
#
# def test_mip_dna_load_observations(
#     case_id: str,
#     mip_dna_observations_api: MipDNAObservationsAPI,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
#     mocker: MockFixture,
# ):
#     """Test loading of case observations for rare disease."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mock MIP DNA observations API and a list of observations input files
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#
#     # WHEN loading the case to Loqusdb
#     mip_dna_observations_api.load_observations(case)
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
#     mocker: MockFixture,
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
#     mocker: MockFixture,
# ):
#     """Test loading of a tumor case to Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a MIP DNA observations API and a case object with a tumour sample
#     case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(mip_dna_observations_api, "is_duplicate", return_value=False)
#     case.links[0].sample.is_tumour = True
#     mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS)
#     mocker.patch.object(mip_dna_observations_api, "set_loqusdb_instance", return_value=None)
#     mocker.patch.object(
#         mip_dna_observations_api,
#         "get_observations_input_files",
#         return_value=observations_input_files,
#     )
#
#     # WHEN getting the Loqusdb API
#     with pytest.raises(LoqusdbUploadCaseError):
#         # THEN an upload error should be raised and the execution aborted
#         mip_dna_observations_api.load_observations(case)
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
# def test_balsamic_load_observations(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     balsamic_observations_input_files: BalsamicObservationsInputFiles,
#     nr_of_loaded_variants: int,
#     caplog: LogCaptureFixture,
#     mocker: MockFixture,
# ):
#     """Test loading of cancer case observations."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a mock BALSAMIC observations API and a list of observations input files
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(balsamic_observations_api, "is_duplicate", return_value=False)
#     mocker.patch.object(AnalysisAPI, "get_data_analysis_type", return_value=SequencingMethod.WGS)
#     mocker.patch.object(
#         balsamic_observations_api,
#         "get_observations_input_files",
#         return_value=balsamic_observations_input_files,
#     )
#     # WHEN loading the case to Loqusdb
#     balsamic_observations_api.load_observations(case)
#
#     # THEN the observations should be loaded successfully
#     assert f"Uploaded {nr_of_loaded_variants} variants to Loqusdb" in caplog.text
#
#
# def test_balsamic_load_observations_duplicate(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     observations_input_files: MipDNAObservationsInputFiles,
#     caplog: LogCaptureFixture,
#     mocker: MockFixture,
# ):
#     """Test upload cancer duplicate case observations to Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a balsamic observations API and a case object that has already been uploaded to Loqusdb
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(internal_id=case_id)
#     mocker.patch.object(balsamic_observations_api, "is_duplicate", return_value=True)
#
#     # WHEN uploading the case observations to Loqusdb
#     with pytest.raises(LoqusdbDuplicateRecordError):
#         # THEN a duplicate record error should be raised
#         balsamic_observations_api.load_observations(case)
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
