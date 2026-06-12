from pathlib import Path
from unittest.mock import Mock

import click
import pytest
from mock import create_autospec
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.models.cg_config import (
    BalsamicConfig,
    CGConfig,
    IlluminaConfig,
    RunInstruments,
    SlurmConfig,
)
from cg.store.models import Analysis, Case
from cg.store.store import Store


@pytest.fixture
def cg_config() -> CGConfig:
    return create_autospec(
        CGConfig,
        balsamic=create_autospec(
            BalsamicConfig,
            balsamic_cache=Path("balsamic_cache"),
            bed_path=Path("bed_path"),
            binary_path="balsamic_binary",
            cache_version="autospec_data",
            cadd_path="autospec_data",
            cancer_genelist="autospec_data",
            conda_binary="autospec_data",
            conda_env="autospec_data",
            cosmic_path="autospec_data",
            genome_interval_path="autospec_data",
            gens_coverage_female_path="autospec_data",
            gens_coverage_male_path="autospec_data",
            gnomad_af5_path="autospec_data",
            head_job_partition="autospec_data",
            loqusdb_path="autospec_data",
            pon_path="pon_path",
            slurm=create_autospec(
                SlurmConfig,
                account="account",
                mail_user="mail@clinicalgenomics.se",
                qos="high",
            ),
            root="root",
            sentieon_licence_path="autospec_data",
            sentieon_licence_server="autospec_data",
            swegen_path="autospec_drata",
            swegen_snv="rautospec_data",
            swegen_sv="rautospec_data",
        ),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )


def test_upload_with_case_uploading_to_customer_inbox(cg_config: CGConfig, mocker: MockerFixture):
    # GIVEN a store with an analysis
    analysis: Analysis = create_autospec(Analysis)
    case: Case = create_autospec(Case, is_to_be_uploaded_to_customer_inbox=True)
    status_db: Store = create_autospec(Store, session=create_autospec(Session))
    status_db.get_latest_completed_analysis_for_case = Mock(return_value=analysis)
    cg_config.status_db = status_db
    balsamic_upload_api = BalsamicUploadAPI(config=cg_config)
    balsamic_upload_api.upload_files_to_customer_inbox = Mock()
    update_uploaded_at_spy = mocker.spy(BalsamicUploadAPI, "update_uploaded_at")

    # WHEN uploading a case
    balsamic_upload_api.upload(ctx=create_autospec(click.Context), case=case, restart=False)

    # THEN files should have been uploaded to the customer inbox
    balsamic_upload_api.upload_files_to_customer_inbox.assert_called_once_with(case)

    # THEN the analysis uploaded_at is not set yet
    update_uploaded_at_spy.assert_not_called()


def test_upload_with_case_not_uploading_to_customer_inbox(
    cg_config: CGConfig, mocker: MockerFixture
):
    # GIVEN a store with an analysis
    analysis: Analysis = create_autospec(Analysis)
    case: Case = create_autospec(Case, is_to_be_uploaded_to_customer_inbox=False)
    status_db: Store = create_autospec(Store, session=create_autospec(Session))
    status_db.get_latest_completed_analysis_for_case = Mock(return_value=analysis)
    cg_config.status_db = status_db
    balsamic_upload_api = BalsamicUploadAPI(config=cg_config)
    balsamic_upload_api.upload_files_to_customer_inbox = Mock()
    update_uploaded_at_spy = mocker.spy(BalsamicUploadAPI, "update_uploaded_at")

    # WHEN uploading a case
    balsamic_upload_api.upload(ctx=create_autospec(click.Context), case=case, restart=False)

    # THEN files should have been uploaded to the customer inbox
    balsamic_upload_api.upload_files_to_customer_inbox.assert_not_called()

    # THEN the analysis uploaded at is set
    update_uploaded_at_spy.assert_called_once()
