"""Tests API upload methods for balsamic cases"""

from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from tests.cli.workflow.balsamic.conftest import *


def test_genotype_check_wgs_normal(balsamic_context):
    """Test a balsamic case with WGS and Normal sample that is genotype compatible"""
    # GIVEN a balsamic case with WGS tag and a normal sample
    internal_id = "balsamic_case_wgs_paired_enough_reads"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if genotype upload compatible
    genotype_check = UploadGenotypesAPI.genotype_check(case_obj)

    # THEN it should return True, genotype compatible
    assert genotype_check == True


def test_genotype_check_non_wgs_normal(balsamic_context):
    """Test a balsamic case with no WGS sample that is not genotype compatible"""
    # GIVEN a balsamic case with a normal sample but no WGS tag
    internal_id = "balsamic_case_tgs_paired"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if genotype upload compatible
    genotype_check = balsamic_context.genotype_check(case_obj)

    # THEN it should return False, not genotype compatible
    assert genotype_check == False


def test_genotype_check_only_tumour(balsamic_context):
    """Test a balsamic case with only a tumour sample that is not genotype compatible"""
    # GIVEN a balsamic case with only tumour sample
    internal_id = "balsamic_case_wgs_single"
    case_obj: models.Family = balsamic_context.status_db.family(internal_id=internal_id)

    # WHEN checking if genotype upload compatible
    genotype_check = balsamic_context.genotype_check(case_obj)

    # THEN it should return False, not genotype compatible
    assert genotype_check == False
