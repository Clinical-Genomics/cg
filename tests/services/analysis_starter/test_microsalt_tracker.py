from pathlib import Path
from unittest.mock import create_autospec

import mock
import pytest

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import Workflow, WorkflowManager
from cg.constants.tb import AnalysisStatus, AnalysisType
from cg.exc import AnalysisRunningError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.microsalt import MicrosaltTracker
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.fixture
def microsalt_tracker(cg_context: CGConfig, microsalt_store: Store):
    return MicrosaltTracker(
        store=microsalt_store,
        subprocess_submitter=SubprocessSubmitter(),
        trailblazer_api=cg_context.trailblazer_api,
        workflow_root=cg_context.microsalt.root,
    )


def test_microsalt_tracker_successful(microsalt_tracker: MicrosaltTracker, microsalt_store: Store):
    # GIVEN a microSALT case config
    case_config = MicrosaltCaseConfig(
        case_id="microparakeet",
        binary="binary",
        conda_binary="conda/binary",
        config_file="config/file",
        environment="stage",
        fastq_directory="fastq/dir",
    )
    case_id: str = case_config.case_id

    # WHEN wanting to track the started microSALT analysis
    with mock.patch.object(
        TrailblazerAPI,
        "query_trailblazer",
        return_value={
            "id": 123456,
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "",
            "config_path": "",
        },
    ) as request_submitter:
        microsalt_tracker.track(case_config)

    # THEN the appropriate POST should have been sent
    case: Case = microsalt_store.get_case_by_internal_id(case_id)
    config_path: Path = microsalt_tracker._get_job_ids_path(case_id)
    expected_request_body: dict = {
        "case_id": case_id,
        "email": environ_email(),
        "type": AnalysisType.OTHER,
        "config_path": config_path.as_posix(),
        "order_id": case.latest_order.id,
        "out_dir": config_path.parent.as_posix(),
        "priority": microsalt_tracker._get_trailblazer_priority(case_id),
        "workflow": Workflow.MICROSALT.upper(),
        "ticket": str(case.latest_order.ticket_id),
        "workflow_manager": WorkflowManager.Slurm,
        "tower_workflow_id": None,
        "is_hidden": True,
    }
    request_submitter.assert_called_with(
        command="add-pending-analysis", request_body=expected_request_body
    )


def test_get_job_ids_path_multiple_samples(microsalt_tracker: MicrosaltTracker):

    # GIVEN a microSALT case containing two samples
    microsalt_case = create_autospec(Case)
    internal_id = "case_id"
    microsalt_case.internal_id = internal_id
    sample_1 = create_autospec(Sample)
    sample_2 = create_autospec(Sample)
    sample_1.internal_id = "ACC123A1"
    microsalt_case.samples = [sample_1, sample_2]
    store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = microsalt_case
    microsalt_tracker.store = store

    # WHEN getting the job_ids_path
    job_id_path: Path = microsalt_tracker._get_job_ids_path(internal_id)

    # THEN the file name should use the LIMS project ID
    assert job_id_path.name == "ACC123_slurm_ids.yaml"


def test_get_job_ids_path_single_sample(microsalt_tracker: MicrosaltTracker):

    # GIVEN a microSALT case containing two samples
    microsalt_case = create_autospec(Case)
    internal_id = "case_id"
    microsalt_case.internal_id = internal_id
    sample = create_autospec(Sample)
    sample.internal_id = "ACC123A1"
    microsalt_case.samples = [sample]
    store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = microsalt_case
    microsalt_tracker.store = store

    # WHEN getting the job_ids_path
    job_id_path: Path = microsalt_tracker._get_job_ids_path(internal_id)

    # THEN the file name should use the sample ID
    assert job_id_path.name == "ACC123A1_slurm_ids.yaml"


def test_microsalt_tracker_ongoing_analysis(microsalt_tracker: MicrosaltTracker):
    # GIVEN that we try to run a case whose latest analysis is still running

    # WHEN ensuring that the latest analysis is _not_ running

    # THEN a CgError should be raised
    with (
        mock.patch.object(
            TrailblazerAPI, "get_latest_analysis_status", return_value=AnalysisStatus.RUNNING
        ),
        pytest.raises(AnalysisRunningError),
    ):
        microsalt_tracker.ensure_analysis_not_ongoing("case_id")
