"""Test the Gens upload command."""

from unittest.mock import ANY, Mock, call, create_autospec

import pytest
from click.testing import CliRunner

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import GenomeBuild, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "workflow, expected_genome_build",
    [(Workflow.RAREDISEASE, GenomeBuild.hg19), (Workflow.NALLO, GenomeBuild.hg38)],
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
    status_db.get_case_by_internal_id = Mock(return_value=case)

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
