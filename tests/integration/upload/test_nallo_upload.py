"""Integration test for the upload command for a NALLO case."""

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import (
    IntegrationTestPaths,
    create_empty_file,
    create_integration_test_sample_bam_files,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture
def nallo_case(helpers: StoreHelpers, status_db: Store) -> Case:
    return helpers.add_case(store=status_db, data_analysis=Workflow.NALLO)


@pytest.fixture
def nallo_sample(
    housekeeper_db: HousekeeperStore, status_db: Store, test_run_paths: IntegrationTestPaths
) -> Sample:
    return create_integration_test_sample_bam_files(
        status_db=status_db, housekeeper_db=housekeeper_db, test_run_paths=test_run_paths
    )


@pytest.fixture
def nallo_case_bundle(
    nallo_case: Case,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
) -> tuple[Bundle, Version]:
    """Create a Housekeeper bundle for the NALLO case with required upload files."""
    case_files = {
        "delivery-report.html": ["delivery-report"],
        "snv_clinical.vcf.gz": ["vcf-snv-clinical"],
        "snv_research.vcf.gz": ["vcf-snv-research"],
        "sv_clinical.vcf.gz": ["vcf-sv-clinical"],
        "sv_research.vcf.gz": ["vcf-sv-research"],
    }
    hk_files = []
    for filename, tags in case_files.items():
        file_path = Path(test_run_paths.test_root_dir, filename)
        create_empty_file(file_path)
        hk_files.append({"path": file_path.as_posix(), "archive": False, "tags": tags})

    bundle_data = {
        "name": nallo_case.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": hk_files,
    }
    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()
    return bundle, version


@pytest.fixture
def nallo_analysis(
    helpers: StoreHelpers,
    status_db: Store,
    nallo_case: Case,
    nallo_case_bundle: tuple[Bundle, Version],
) -> Analysis:
    """Create a completed NALLO analysis."""
    _, version = nallo_case_bundle
    return helpers.add_analysis(
        store=status_db,
        case=nallo_case,
        workflow=Workflow.NALLO,
        completed_at=datetime.now(),
        housekeeper_version_id=version.id,  # type: ignore
    )


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_upload_nallo(
    helpers: StoreHelpers,
    httpserver: HTTPServer,
    mock_run_commands: Callable,
    mocker: MockerFixture,
    nallo_analysis: Analysis,
    nallo_case: Case,
    nallo_sample: Sample,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
):
    """Test a successful run of 'cg upload -c CASE_ID' for a NALLO case."""
    cli_runner = CliRunner()

    # GIVEN a NALLO case with a related sample and a completed analysis
    helpers.relate_samples(base_store=status_db, case=nallo_case, samples=[nallo_sample])

    # GIVEN the case output directory exists (required for saving the Scout load config)
    case_directory = Path(test_run_paths.test_root_dir, "nallo_root_path", nallo_case.internal_id)
    case_directory.mkdir(parents=True, exist_ok=True)

    # GIVEN Scout can be called
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # GIVEN the Trailblazer API accepts the upload status update
    httpserver.expect_request("/trailblazer/set-analysis-uploaded", method="PUT").respond_with_json(
        None
    )

    # WHEN running the upload command for the NALLO case
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            test_run_paths.cg_config_file.as_posix(),
            "upload",
            "-c",
            nallo_case.internal_id,
        ],
        catch_exceptions=False,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the analysis upload timestamps have been set correctly
    status_db.session.refresh(nallo_analysis)
    started_at = nallo_analysis.upload_started_at
    uploaded_at = nallo_analysis.uploaded_at
    one_hour_ago = datetime.now() - timedelta(hours=1)

    assert started_at and uploaded_at
    assert uploaded_at > started_at
    assert started_at > one_hour_ago
    assert uploaded_at > one_hour_ago
