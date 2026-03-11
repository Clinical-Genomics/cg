from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, call, create_autospec

import pytest
from click import Context

from cg.constants.constants import DataDelivery
from cg.meta.upload.nallo.nallo_upload_api import (
    NalloUploadAPI,
    generate_delivery_report,
    upload_observations_to_loqusdb,
    upload_to_gens,
    upload_to_scout,
)
from cg.models.cg_config import CGConfig, IlluminaConfig, NalloConfig, RunInstruments, SlurmConfig
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Analysis, Case
from cg.store.store import Store


@pytest.mark.freeze_time
def test_upload_succeeds():
    # GIVEN the file delivery service can be created for this use case
    deliver_files_service = create_autospec(DeliverFilesService)

    delivery_service_factory: DeliveryServiceFactory = create_autospec(DeliveryServiceFactory)
    delivery_service_factory.build_delivery_service = Mock(return_value=deliver_files_service)

    # GIVEN a cg config with necessary contents for Nallo and a connection to StatusDB
    status_db = create_autospec(Store, session=Mock())
    cg_config = create_autospec(
        CGConfig,
        delivery_path="delivery/path",
        delivery_service_factory=delivery_service_factory,
        nallo=create_autospec(
            NalloConfig,
            conda_env="nallo_conda_env",
            conda_binary="nallo_conda_binary",
            config="nallo_config",
            params="nallo_params",
            platform="nallo_platform",
            profile="nallo_profile",
            resources="nallo_resources",
            revision="nallo_revision",
            root="root/dir",
            slurm=create_autospec(
                SlurmConfig, account="nallo_slurm_account", mail_user="slurm_user@scilifelab.se"
            ),
            tower_workflow="nallo_tower_workflow",
            workflow_bin_path="workflow/bin/path",
        ),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
        status_db=status_db,
        tower_binary_path="tower/binary/path",
    )

    # GIVEN a case with analysis and scout delivery and a completed analysis
    case = create_autospec(Case, internal_id="case_id", data_delivery=DataDelivery.ANALYSIS_SCOUT)
    analysis = create_autospec(Analysis)

    status_db.get_latest_completed_analysis_for_case = lambda internal_id: (
        analysis if internal_id == case.internal_id else None
    )

    # GIVEN an instance of the NalloUploadAPI
    nallo_upload_api = NalloUploadAPI(config=cg_config)

    # GIVEN a click context is provided
    click_context = create_autospec(Context)

    # WHEN upload is called
    nallo_upload_api.upload(ctx=click_context, case=case, restart=False)

    # THEN a delivery report has been generated and the case has been uploaded to scout and loqusdb
    invoke_calls = [
        call(generate_delivery_report, case_id="case_id"),
        call(upload_to_scout, case_id="case_id", re_upload=False),
        call(upload_observations_to_loqusdb, case_id="case_id"),
        call(upload_to_gens, case_id="case_id"),
    ]

    click_context.invoke.assert_has_calls(invoke_calls)

    # THEN the files for the case has been delivered
    deliver_files_service.deliver_files_for_case.assert_called_once_with(
        case=case, delivery_base_path=Path("delivery/path")
    )

    # THEN the analysis has been updated with the current time for upload_started_at and uploaded_at
    assert analysis.upload_started_at == datetime.now()
    assert analysis.uploaded_at == datetime.now()
