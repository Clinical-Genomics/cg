"""Tests API upload methods for balsamic cases"""

from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from tests.cli.workflow.balsamic.conftest import (
    fixture_balsamic_context,
    balsamic_lims,
    balsamic_housekeeper,
    balsamic_mock_fastq_files,
    balsamic_housekeeper_dir,
    fastq_file_l_1_r_1,
    fastq_file_l_1_r_2,
    fastq_file_l_2_r_1,
    fastq_file_l_2_r_2,
    fastq_file_l_3_r_1,
    fastq_file_l_3_r_2,
    fastq_file_l_4_r_1,
    fastq_file_l_4_r_2,
)


def test_genotype_check_wgs_normal(balsamic_context: CGConfig):
    """Test a cancer case with WGS and normal sample that is Genotype compatible."""
    # GIVEN a balsamic case with WGS tag and a normal sample
    internal_id = "balsamic_case_wgs_paired_enough_reads"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case_obj)

    # THEN it should return True
    assert passed_check


def test_genotype_check_non_wgs_normal(balsamic_context: CGConfig):
    """Test a cancer case with no WGS sample that is not Genotype compatible."""
    # GIVEN a balsamic case with a normal sample, but no WGS tag
    internal_id = "balsamic_case_tgs_paired"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case_obj)

    # THEN it should return False
    assert not passed_check


def test_genotype_check_only_tumour(balsamic_context: CGConfig):
    """Test a cancer case with only a tumour sample that is not Genotype compatible."""
    # GIVEN a balsamic case with only tumour sample
    internal_id = "balsamic_case_wgs_single"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if the case is Genotype upload compatible
    passed_check = UploadGenotypesAPI.is_suitable_for_genotype_upload(case_obj)

    # THEN it should return False
    assert not passed_check
