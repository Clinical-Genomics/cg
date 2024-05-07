"""Test Balsamic observations API."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CancerAnalysisType
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sample_sources import SourceType
from cg.exc import LoqusdbDuplicateRecordError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import Case, Customer


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


def test_is_analysis_type_not_eligible_for_observations_upload(
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


def test_is_case_eligible_for_observations_upload(
    case_id: str,
    balsamic_customer: Customer,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
):
    """Test whether a case is eligible for Balsamic observation uploads."""

    # GIVEN a case and a Balsamic observations API
    case: Case = balsamic_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a balsamic customer, and eligible sequencing method, and a case with tumor samples
    case.customer.internal_id = balsamic_customer.internal_id
    mocker.patch.object(
        BalsamicAnalysisAPI, "get_data_analysis_type", return_value=CancerAnalysisType.TUMOR_WGS
    )
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should be eligible for observation uploads
    assert is_case_eligible_for_observations_upload


def test_is_case_not_eligible_for_observations_upload(
    case_id: str,
    balsamic_customer: Customer,
    balsamic_observations_api: BalsamicObservationsAPI,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test whether a case is eligible for Balsamic observation uploads."""

    # GIVEN a case and a Balsamic observations API
    case: Case = balsamic_observations_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a balsamic customer, a case with tumor samples, and an invalid sequencing type
    case.customer.internal_id = balsamic_customer.internal_id
    mocker.patch.object(
        BalsamicAnalysisAPI, "get_data_analysis_type", return_value=CancerAnalysisType.TUMOR_PANEL
    )
    mocker.patch.object(BalsamicAnalysisAPI, "is_analysis_normal_only", return_value=False)
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN checking the upload eligibility for a case
    is_case_eligible_for_observations_upload: bool = (
        balsamic_observations_api.is_case_eligible_for_observations_upload(case)
    )

    # THEN the case should not be eligible for observation uploads
    assert not is_case_eligible_for_observations_upload


def test_load_observations(
    case_id: str,
    loqusdb_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    number_of_loaded_variants: int,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of Balsamic case observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a list of input files for upload
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)
    mocker.patch.object(
        BalsamicObservationsAPI,
        "get_observations_input_files",
        return_value=balsamic_observations_input_files,
    )

    # GIVEN a Loqusdb mocked scenario
    mocker.patch.object(BalsamicObservationsAPI, "is_duplicate", return_value=False)
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )

    # WHEN loading the case to Loqusdb
    balsamic_observations_api.load_observations(case)

    # THEN the observations should be loaded successfully
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


def test_load_duplicated_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
):
    """Test loading of Balsamic case observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API and a Balsamic case
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # GIVEN a duplicate case in Loqusdb
    mocker.patch.object(BalsamicObservationsAPI, "is_duplicate", return_value=True)

    # WHEN loading the case to Loqusdb
    with pytest.raises(LoqusdbDuplicateRecordError):
        balsamic_observations_api.load_observations(case)

    # THEN the observations upload should be aborted
    assert f"Case {case.internal_id} has already been uploaded to Loqusdb" in caplog.text


def test_load_cancer_observations(
    case_id: str,
    balsamic_observations_api: BalsamicObservationsAPI,
    balsamic_observations_input_files: BalsamicObservationsInputFiles,
    number_of_loaded_variants: int,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test loading of case observations for Balsamic."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Balsamic observations API, a list of input files, and a cancer case
    case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)

    # GIVEN a mocked return from the Loqusdb API
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        BalsamicAnalysisAPI,
        "get_data_analysis_type",
        return_value=CancerAnalysisType.TUMOR_NORMAL_WGS,
    )

    # WHEN loading the case to a somatic Loqusdb instance
    balsamic_observations_api.load_cancer_observations(
        case=case,
        input_files=balsamic_observations_input_files,
        loqusdb_api=balsamic_observations_api.loqusdb_somatic_api,
    )

    # THEN the observations should be loaded successfully
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


# def test_balsamic_delete_case(
#     case_id: str,
#     balsamic_observations_api: BalsamicObservationsAPI,
#     caplog: LogCaptureFixture,
# ):
#     """Test delete balsamic case observations from Loqusdb."""
#     caplog.set_level(logging.DEBUG)
#
#     # GIVEN a Loqusdb instance and a case that has been uploaded to both somatic and tumor instances
#     case: Case = balsamic_observations_api.store.get_case_by_internal_id(case_id)
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
