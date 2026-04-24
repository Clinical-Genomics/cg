from datetime import datetime
from pathlib import Path
from typing import cast

import pytest
import yaml
from click.testing import CliRunner, Result
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store
from tests.integration.utils import (
    IntegrationTestPaths,
    create_empty_file,
    expect_lims_sample_and_project,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture
def nallo_case(helpers: StoreHelpers, status_db: Store) -> Case:
    return helpers.add_case(store=status_db, data_analysis=Workflow.NALLO)


@pytest.fixture
def nallo_sample(helpers: StoreHelpers, status_db: Store) -> Sample:
    return helpers.add_sample(
        application_type="wgs",
        store=status_db,
        last_sequenced_at=datetime.now(),
    )


@pytest.fixture
def nallo_hk_bundle(
    nallo_case: Case,
    nallo_sample: Sample,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
) -> Version:
    """Create a Housekeeper bundle for a Nallo case with the minimum required analysis files."""
    root = test_run_paths.test_root_dir
    sample_id = nallo_sample.internal_id

    vcf_snv = Path(root, "vcf_snv_clinical.vcf")
    vcf_snv_research = Path(root, "vcf_snv_research.vcf")
    vcf_sv = Path(root, "vcf_sv_clinical.vcf")
    vcf_sv_research = Path(root, "vcf_sv_research.vcf")
    delivery_report = Path(root, "delivery_report.html")
    bam_file = Path(root, f"{sample_id}.bam")

    for path in [vcf_snv, vcf_snv_research, vcf_sv, vcf_sv_research, delivery_report, bam_file]:
        create_empty_file(path)

    bundle_data = {
        "name": nallo_case.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {"path": vcf_snv.as_posix(), "tags": ["vcf-snv-clinical"], "archive": False},
            {"path": vcf_snv_research.as_posix(), "tags": ["vcf-snv-research"], "archive": False},
            {"path": vcf_sv.as_posix(), "tags": ["vcf-sv-clinical"], "archive": False},
            {"path": vcf_sv_research.as_posix(), "tags": ["vcf-sv-research"], "archive": False},
            {"path": delivery_report.as_posix(), "tags": ["delivery-report"], "archive": False},
            {
                "path": bam_file.as_posix(),
                "tags": [AlignmentFileTag.BAM, "haplotags", sample_id],
                "archive": False,
            },
        ],
    }

    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()
    return version


@pytest.fixture
def nallo_completed_analysis(
    helpers: StoreHelpers,
    nallo_case: Case,
    nallo_hk_bundle: Version,
    nallo_sample: Sample,
    status_db: Store,
) -> Analysis:
    helpers.relate_samples(base_store=status_db, case=nallo_case, samples=[nallo_sample])
    return helpers.add_analysis(
        store=status_db,
        case=nallo_case,
        workflow=Workflow.NALLO,
        completed_at=datetime.now(),
    )


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_create_nallo_scout_load_config_serializes_correctly(
    httpserver: HTTPServer,
    nallo_case: Case,
    nallo_completed_analysis: Analysis,
    nallo_sample: Sample,
    test_run_paths: IntegrationTestPaths,
):
    """Test that the generated scout_load.yaml contains correctly serialized values."""
    cli_runner = CliRunner()

    # GIVEN the case output directory exists
    case_dir = Path(test_run_paths.test_root_dir, "nallo_root_path", nallo_case.internal_id)
    case_dir.mkdir(parents=True, exist_ok=True)

    # GIVEN the LIMS server handles the sample and project metadata requests
    expect_lims_sample_and_project(httpserver=httpserver, sample=nallo_sample)

    # WHEN generating the scout load config via the CLI
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            test_run_paths.cg_config_file.as_posix(),
            "upload",
            "create-scout-load-config",
            nallo_case.internal_id,
        ],
        catch_exceptions=False,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0, result.output

    # THEN the scout_load.yaml file exists at the expected path
    scout_load_config_path = Path(case_dir, "scout_load.yaml")
    assert scout_load_config_path.exists()

    # THEN the YAML can be loaded into a dict without errors
    with open(scout_load_config_path) as config_file_handle:
        config: dict = yaml.safe_load(config_file_handle)
        assert isinstance(config, dict)
