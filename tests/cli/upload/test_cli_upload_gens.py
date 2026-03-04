"""Test the Gens upload command."""

from typing import cast
from unittest.mock import ANY, Mock, call, create_autospec

import pytest
from click.testing import CliRunner
from housekeeper.store.models import File

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import GenomeBuild, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.fixture()
def upload_gens_context():
    return create_autospec(
        CGConfig,
        status_db=create_autospec(Store),
        housekeeper_api=create_autospec(HousekeeperAPI),
        gens_api=create_autospec(GensAPI),
    )


@pytest.mark.parametrize(
    "workflow, expected_genome_build",
    [(Workflow.BALSAMIC, GenomeBuild.hg19), (Workflow.NALLO, GenomeBuild.hg38)],
)
def test_upload_to_gens(
    workflow,
    expected_genome_build,
    cli_runner: CliRunner,
):
    # GIVEN a case with two samples
    sample1 = create_autospec(Sample, internal_id="sample1")
    sample2 = create_autospec(Sample, internal_id="sample2")

    case: Case = create_autospec(
        Case, data_analysis=workflow, internal_id="case_id", samples=[sample1, sample2]
    )

    # GIVEN StatusDB, GensAPI and HousekeeperAPI is available
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    gens_api = create_autospec(GensAPI)

    cg_config = create_autospec(
        CGConfig,
        status_db=status_db,
        housekeeper_api=create_autospec(HousekeeperAPI),
        gens_api=gens_api,
    )

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, ["case_id"], obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the two samples where uploaded using the expected genome build
    gens_api.load.assert_has_calls(
        [
            call(
                baf_path=ANY,
                case_id="case_id",
                coverage_path=ANY,
                genome_build=expected_genome_build,
                sample_id="sample1",
            ),
            call(
                baf_path=ANY,
                case_id="case_id",
                coverage_path=ANY,
                genome_build=expected_genome_build,
                sample_id="sample2",
            ),
        ]
    )


@pytest.mark.parametrize(
    "workflow, genome_build",
    [
        (Workflow.BALSAMIC, GenomeBuild.hg19),
        (Workflow.BALSAMIC_UMI, GenomeBuild.hg19),
        (Workflow.MIP_DNA, GenomeBuild.hg19),
        (Workflow.RAREDISEASE, GenomeBuild.hg38),
    ],
)
def test_upload_gens_genome_build(
    workflow: Workflow,
    genome_build: GenomeBuild,
    cli_runner: CliRunner,
    upload_gens_context: CGConfig,
):
    # GIVEN store and gens APIs
    # GIVEN a case with a sample
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    case: Case = create_autospec(Case, data_analysis=workflow, samples=[sample])
    upload_gens_context.status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a HousekeeperAPI
    file_path = "/path/to/file"
    upload_gens_context.housekeeper_api.get_file_from_latest_version = Mock(
        return_value=create_autospec(File, full_path=file_path)
    )

    # WHEN uploading to gens
    cli_runner.invoke(upload_gens_cmd, ["some_case"], obj=upload_gens_context)

    # THEN assert gens is called with correct genome build
    cast(Mock, upload_gens_context.gens_api).load.assert_called_once_with(
        baf_path=file_path,
        case_id="some_case",
        coverage_path=file_path,
        genome_build=genome_build,
        sample_id="sample_id",
    )
