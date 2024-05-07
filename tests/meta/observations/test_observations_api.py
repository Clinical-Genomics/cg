"""Test observations API methods."""

import logging
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CancerAnalysisType, CustomerId, Workflow
from cg.constants.observations import LOQUSDB_ID, LoqusdbInstance, MipDNALoadParameters
from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbUploadCaseError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case, Customer


@pytest.mark.parametrize(
    "workflow, analysis_api, sequencing_method, is_tumour",
    [
        (Workflow.BALSAMIC, BalsamicAnalysisAPI, CancerAnalysisType.TUMOR_WGS, True),
        (Workflow.MIP_DNA, MipDNAAnalysisAPI, SequencingMethod.WGS, False),
    ],
)
def test_observations_upload(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    workflow: Workflow,
    analysis_api: AnalysisAPI,
    sequencing_method: str,
    is_tumour: bool,
    request: FixtureRequest,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test upload of observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API, a list of observation input files, and a workflow customer
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    observations_input_files: MipDNAObservationsInputFiles = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_input_files"
    )
    customer: Customer = request.getfixturevalue(f"{workflow.replace('-', '_')}_customer")

    # GIVEN a case eligible for Loqusdb uploads
    case: Case = observations_api.store.get_case_by_internal_id(case_id)
    case.customer.internal_id = customer.internal_id
    case.samples[0].is_tumour = is_tumour

    # GIVEN a mock scenario for a successful upload
    mocker.patch.object(analysis_api, "get_data_analysis_type", return_value=sequencing_method)
    mocker.patch.object(
        ObservationsAPI, "get_observations_input_files", return_value=observations_input_files
    )
    mocker.patch.object(ObservationsAPI, "is_duplicate", return_value=False)
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    # WHEN uploading the case observations to Loqusdb
    observations_api.upload(case)

    # THEN the case should be successfully uploaded
    assert f"Uploaded {number_of_loaded_variants} variants to Loqusdb" in caplog.text


@pytest.mark.parametrize(
    "workflow, analysis_api, sequencing_method, is_tumour",
    [
        (Workflow.BALSAMIC, BalsamicAnalysisAPI, CancerAnalysisType.TUMOR_WGS, True),
        (Workflow.MIP_DNA, MipDNAAnalysisAPI, SequencingMethod.WGS, False),
    ],
)
def test_observations_upload_not_eligible(
    case_id: str,
    loqusdb_id: str,
    number_of_loaded_variants: int,
    workflow: Workflow,
    analysis_api: AnalysisAPI,
    sequencing_method: str,
    is_tumour: bool,
    request: FixtureRequest,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test upload of observations."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an observations API, a list of observation input files, and a workflow customer
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    observations_input_files: MipDNAObservationsInputFiles = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_input_files"
    )
    customer: Customer = request.getfixturevalue(f"{workflow.replace('-', '_')}_customer")

    # GIVEN a case eligible for Loqusdb uploads
    case: Case = observations_api.store.get_case_by_internal_id(case_id)
    case.customer.internal_id = customer.internal_id
    case.samples[0].is_tumour = is_tumour

    # GIVEN a mock scenario for an upload with an invalid source type
    mocker.patch.object(analysis_api, "get_data_analysis_type", return_value=sequencing_method)
    mocker.patch.object(
        ObservationsAPI, "get_observations_input_files", return_value=observations_input_files
    )
    mocker.patch.object(ObservationsAPI, "is_duplicate", return_value=False)
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE_FFPE)

    # WHEN uploading the case observations to Loqusdb
    with pytest.raises(LoqusdbUploadCaseError):
        observations_api.upload(case)

    # THEN an upload error should be caught and the upload cancelled
    assert f"Case {case.internal_id} is not eligible for observations upload" in caplog.text


@pytest.mark.parametrize(
    "workflow, loqusdb_instance",
    [(Workflow.BALSAMIC, LoqusdbInstance.TUMOR), (Workflow.MIP_DNA, LoqusdbInstance.WES)],
)
def test_get_loqusdb_api(
    cg_context: CGConfig,
    workflow: Workflow,
    loqusdb_instance: LoqusdbInstance,
    request: FixtureRequest,
):
    """Test Loqusdb API retrieval given a Loqusdb instance."""

    # GIVEN a WES Loqusdb instance and an observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )

    # GIVEN the expected Loqusdb config dictionary
    loqusdb_instance_key: str = loqusdb_instance.value.replace("-", "_")
    loqusdb_config: dict[str, Path] = cg_context.dict()[loqusdb_instance_key]

    # WHEN calling the Loqusdb API get method
    loqusdb_api: LoqusdbAPI = observations_api.get_loqusdb_api(loqusdb_instance)

    # THEN a WES Loqusdb API should be returned
    assert isinstance(loqusdb_api, LoqusdbAPI)
    assert loqusdb_api.binary_path == loqusdb_config["binary_path"]
    assert loqusdb_api.config_path == loqusdb_config["config_path"]


@pytest.mark.parametrize(
    "workflow, loqusdb_instance",
    [(Workflow.BALSAMIC, LoqusdbInstance.TUMOR), (Workflow.MIP_DNA, LoqusdbInstance.WES)],
)
def test_is_not_duplicate(
    case_id: str,
    workflow: Workflow,
    loqusdb_instance: LoqusdbInstance,
    request: FixtureRequest,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that is not in Loqusdb."""

    # GIVEN an observations API and a list of files to upload
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    observations_input_files: MipDNAObservationsInputFiles = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_input_files"
    )

    # GIVEN a Loqusdb instance with no case duplicates
    case: Case = observations_api.store.get_case_by_internal_id(case_id)
    loqusdb_api: LoqusdbAPI = observations_api.get_loqusdb_api(loqusdb_instance)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=observations_input_files.snv_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN there should be no duplicates in Loqusdb
    assert is_duplicate is False


@pytest.mark.parametrize(
    "workflow, loqusdb_instance",
    [(Workflow.BALSAMIC, LoqusdbInstance.TUMOR), (Workflow.MIP_DNA, LoqusdbInstance.WES)],
)
def test_is_duplicate(
    case_id: str,
    workflow: Workflow,
    loqusdb_instance: LoqusdbInstance,
    request: FixtureRequest,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN an observations API and a list of files to upload
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    observations_input_files: MipDNAObservationsInputFiles = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_input_files"
    )

    # GIVEN a Loqusdb instance with a duplicated case
    case: Case = observations_api.store.get_case_by_internal_id(case_id)
    loqusdb_api: LoqusdbAPI = observations_api.get_loqusdb_api(loqusdb_instance)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value={"case_id": case_id})

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=observations_input_files.snv_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN an upload of a duplicate case should be detected
    assert is_duplicate is True


@pytest.mark.parametrize(
    "workflow, loqusdb_instance",
    [(Workflow.BALSAMIC, LoqusdbInstance.TUMOR), (Workflow.MIP_DNA, LoqusdbInstance.WES)],
)
def test_is_duplicate_loqusdb_id(
    case_id: str,
    loqusdb_id: str,
    workflow: Workflow,
    loqusdb_instance: LoqusdbInstance,
    request: FixtureRequest,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN an observations API and a list of files to upload
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    observations_input_files: MipDNAObservationsInputFiles = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_input_files"
    )

    # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
    case: Case = observations_api.store.get_case_by_internal_id(case_id)
    loqusdb_api: LoqusdbAPI = observations_api.get_loqusdb_api(loqusdb_instance)
    case.links[0].sample.loqusdb_id = loqusdb_id
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that the sample observations have already been uploaded
    is_duplicate: bool = observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=observations_input_files.snv_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN a duplicated upload should be identified
    assert is_duplicate is True


@pytest.mark.parametrize("workflow", [Workflow.BALSAMIC, Workflow.MIP_DNA])
def test_is_customer_eligible_for_observations_upload(
    workflow: Workflow,
    request: FixtureRequest,
):
    """Test if customer is eligible for observations upload."""

    # GIVEN a MIP-DNA customer and observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    customer: Customer = request.getfixturevalue(f"{workflow.replace('-', '_')}_customer")
    customer_id: str = customer.internal_id

    # WHEN verifying if the customer is eligible for Balsamic observations upload
    is_customer_eligible_for_observations_upload: bool = (
        observations_api.is_customer_eligible_for_observations_upload(customer_id)
    )

    # THEN the customer's data should be eligible for uploads
    assert is_customer_eligible_for_observations_upload


@pytest.mark.parametrize("workflow", [Workflow.BALSAMIC, Workflow.MIP_DNA])
def test_is_customer_not_eligible_for_observations_upload(
    workflow: Workflow, request: FixtureRequest, caplog: LogCaptureFixture
):
    """Test if customer is not eligible for observations upload."""

    # GIVEN a CG internal customer ID and observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    customer_id: str = CustomerId.CG_INTERNAL_CUSTOMER

    # WHEN verifying if the customer is eligible for Balsamic observations upload
    is_customer_eligible_for_observations_upload: bool = (
        observations_api.is_customer_eligible_for_observations_upload(customer_id)
    )

    # THEN the customer's data should not be eligible for uploads
    assert not is_customer_eligible_for_observations_upload
    assert f"Customer {customer_id} is not whitelisted for Loqusdb uploads" in caplog.text


@pytest.mark.parametrize(
    "workflow, analysis_api, sequencing_method",
    [
        (Workflow.BALSAMIC, BalsamicAnalysisAPI, CancerAnalysisType.TUMOR_WGS),
        (Workflow.MIP_DNA, MipDNAAnalysisAPI, SequencingMethod.WGS),
    ],
)
def test_is_sequencing_method_eligible_for_observations_upload(
    case_id: str,
    workflow: Workflow,
    analysis_api: AnalysisAPI,
    sequencing_method: str,
    request: FixtureRequest,
    mocker: MockFixture,
):
    """Test if the sequencing method is eligible for observations uploads."""

    # GIVEN a case ID and an observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )

    # GIVEN a supported data analysis type
    mocker.patch.object(analysis_api, "get_data_analysis_type", return_value=sequencing_method)

    # WHEN verifying that the sequencing method is eligible for observations uploads
    is_sequencing_method_eligible_for_observations_upload: bool = (
        observations_api.is_sequencing_method_eligible_for_observations_upload(case_id)
    )

    # THEN the sequencing method should be eligible for observations uploads
    assert is_sequencing_method_eligible_for_observations_upload


@pytest.mark.parametrize(
    "workflow, analysis_api, sequencing_method",
    [
        (Workflow.BALSAMIC, BalsamicAnalysisAPI, CancerAnalysisType.TUMOR_PANEL),
        (Workflow.MIP_DNA, MipDNAAnalysisAPI, SequencingMethod.WTS),
    ],
)
def test_is_sequencing_method_not_eligible_for_observations_upload(
    case_id: str,
    workflow: Workflow,
    analysis_api: AnalysisAPI,
    sequencing_method: str,
    request: FixtureRequest,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the sequencing method is eligible for observations uploads."""

    # GIVEN a case ID and an observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )
    # GIVEN a non-supported data analysis type
    mocker.patch.object(analysis_api, "get_data_analysis_type", return_value=sequencing_method)

    # WHEN verifying that the sequencing method is eligible for observations uploads
    is_sequencing_method_eligible_for_observations_upload: bool = (
        observations_api.is_sequencing_method_eligible_for_observations_upload(case_id)
    )

    # THEN the sequencing method should not be eligible for observations uploads
    assert not is_sequencing_method_eligible_for_observations_upload
    assert (
        f"Sequencing method {sequencing_method} is not supported by Loqusdb uploads" in caplog.text
    )


@pytest.mark.parametrize("workflow", [Workflow.BALSAMIC, Workflow.MIP_DNA])
def test_is_sample_source_eligible_for_observations_upload(
    case_id: str, workflow: Workflow, request: FixtureRequest, mocker: MockFixture
):
    """Test if the sample source is eligible for observations uploads."""

    # GIVEN a case ID and an observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )

    # GIVEN a supported sample source
    source_type = SourceType.TISSUE
    mocker.patch.object(LimsAPI, "get_source", return_value=source_type)

    # WHEN verifying that the sample source is eligible for observations uploads
    is_sample_source_eligible_for_observations_upload: bool = (
        observations_api.is_sample_source_eligible_for_observations_upload(case_id)
    )

    # THEN the source type should be eligible for observations uploads
    assert is_sample_source_eligible_for_observations_upload


@pytest.mark.parametrize("workflow", [Workflow.BALSAMIC, Workflow.MIP_DNA])
def test_is_sample_source_not_eligible_for_observations_upload(
    case_id: str,
    workflow: Workflow,
    request: FixtureRequest,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """Test if the sample source is not eligible for observations uploads."""

    # GIVEN a case ID and an observations API
    observations_api: ObservationsAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_observations_api"
    )

    # GIVEN a not supported sample source
    source_type = SourceType.TISSUE_FFPE
    mocker.patch.object(LimsAPI, "get_source", return_value=source_type)

    # WHEN verifying that the sample source is eligible for observations uploads
    is_sample_source_eligible_for_observations_upload: bool = (
        observations_api.is_sample_source_eligible_for_observations_upload(case_id)
    )

    # THEN the source type should not be eligible for observations uploads
    assert not is_sample_source_eligible_for_observations_upload
    assert f"Source type {source_type} is not supported for Loqusdb uploads" in caplog.text
