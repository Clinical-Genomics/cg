"""Test the Gens upload command."""

from typing import cast
from unittest.mock import ANY, Mock, call, create_autospec

import pytest
from click.testing import CliRunner
from housekeeper.store.models import File

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
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
    "workflow, genome_build",
    [
        (Workflow.BALSAMIC, GenomeBuild.hg19),
        (Workflow.BALSAMIC_UMI, GenomeBuild.hg19),
        (Workflow.MIP_DNA, GenomeBuild.hg19),
        (Workflow.RAREDISEASE, GenomeBuild.hg38),
        (Workflow.NALLO, GenomeBuild.hg38),
    ],
)
def test_upload_gens_genome_build(
    workflow: Workflow,
    genome_build: GenomeBuild,
    cli_runner: CliRunner,
    upload_gens_context: CGConfig,
):
    # GIVEN store and gens APIs
    # GIVEN a case with two samples
    sample1: Sample = create_autospec(Sample, internal_id="sample_id1")
    sample2: Sample = create_autospec(Sample, internal_id="sample_id2")

    case: Case = create_autospec(Case, data_analysis=workflow, samples=[sample1, sample2])
    upload_gens_context.status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a HousekeeperAPI
    file_path = "/path/to/file"
    upload_gens_context.housekeeper_api.get_file_from_latest_version = Mock(
        return_value=create_autospec(File, full_path=file_path)
    )

    # WHEN uploading to gens
    cli_runner.invoke(upload_gens_cmd, ["some_case"], obj=upload_gens_context)

    # THEN both samples were uploaded to gens with correct genome build
    cast(Mock, upload_gens_context.gens_api).load.assert_has_calls(
        [
            call(
                baf_path=ANY,
                case_id="some_case",
                coverage_path=ANY,
                genome_build=genome_build,
                sample_id="sample_id1",
            ),
            call(
                baf_path=ANY,
                case_id="some_case",
                coverage_path=ANY,
                genome_build=genome_build,
                sample_id="sample_id2",
            ),
        ]
    )
