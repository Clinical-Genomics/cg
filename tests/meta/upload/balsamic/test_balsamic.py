"""Tests API upload methods for balsamic cases"""

from unittest.mock import Mock, create_autospec

import click
import pytest
from pytest_mock import MockerFixture

from cg.cli.upload.observations import upload_observations_to_loqusdb
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, RunInstruments
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.store.models import Case
from tests.cli.workflow.balsamic.conftest import balsamic_context


def test_genotype_check_wgs_normal(balsamic_context: CGConfig):
    """Test a cancer case with WHOLE_GENOME_SEQUENCING and normal sample that is Genotype compatible."""
    # GIVEN a balsamic case with WHOLE_GENOME_SEQUENCING tag and a normal sample
    internal_id = "balsamic_case_wgs_paired_enough_reads"
    case: Case = balsamic_context.status_db.get_case_by_internal_id(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case)

    # THEN it should return True
    assert passed_check


def test_genotype_check_non_wgs_normal(balsamic_context: CGConfig):
    """Test a cancer case with no WHOLE_GENOME_SEQUENCING sample that is not Genotype compatible."""
    # GIVEN a balsamic case with a normal sample, but no WHOLE_GENOME_SEQUENCING tag
    internal_id = "balsamic_case_tgs_paired"
    case: Case = balsamic_context.status_db.get_case_by_internal_id(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case)

    # THEN it should return False
    assert not passed_check


def test_genotype_check_only_tumour(balsamic_context: CGConfig):
    """Test a cancer case with only a tumour sample that is not Genotype compatible."""
    # GIVEN a balsamic case with only tumour sample
    internal_id = "balsamic_case_wgs_single"
    case: Case = balsamic_context.status_db.get_case_by_internal_id(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case)

    # THEN it should return False
    assert not passed_check


@pytest.mark.parametrize(
    "prep_category",
    [
        SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
        SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    ],
)
def test_loqusdb_upload_baxsed_on_prep_category_pass(
    prep_category: SeqLibraryPrepCategory, mocker: MockerFixture
):

    # GIVEN a Balsamic Upload API
    upload_api = BalsamicUploadAPI(
        create_autospec(
            CGConfig,
            delivery_path="delivery_path",
            lims_api=Mock(),
            balsamic=Mock(),
            loqusdb=Mock(),
            loqusdb_rd_lwp=Mock(),
            loqusdb_wes=Mock(),
            loqusdb_somatic=Mock(),
            loqusdb_tumor=Mock(),
            loqusdb_somatic_lymphoid=Mock(),
            loqusdb_somatic_myeloid=Mock(),
            loqusdb_somatic_exome=Mock(),
            run_instruments=create_autospec(
                RunInstruments,
                illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="runs_dir"),
            ),
            sentieon_licence_server=Mock(),
            status_db=Mock(),
        ),
    )

    # GIVEN a case containing a sample with a TGS prep category
    case: Case = create_autospec(Case, internal_id="case_id")

    cli_mock = mocker.patch.object(click.Context, "invoke")
    mocker.patch.object(DeliverFilesService, "deliver_files_for_case")
    mocker.patch.object(AnalysisAPI, "get_case_application_type", return_value=prep_category)

    # WHEN uploading
    upload_api.upload(ctx=click.Context(command=Mock()), case=case, restart=False)

    # THEN it should upload observations to LoqusDB
    cli_mock.assert_called_with(upload_observations_to_loqusdb, case_id=case.internal_id)
    assert cli_mock.call_count == 2
