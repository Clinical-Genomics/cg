"""Tests API upload methods for balsamic cases"""

from cg.models.cg_config import CGConfig


def test_genotype_check_wgs_normal(balsamic_context: CGConfig):
    """Test a balsamic case with WGS and Normal sample that is genotype compatible"""
    # GIVEN a balsamic case with WGS tag and a normal sample
    case_obj = balsamic_context.status_db.

    # WHEN checking if genotype upload compatible
    genotype_check = case_obj.genotype_check

    # THEN
    assert genotype_check == True


def test_genotype_check_non_wgs_normal(balsamic_context: CGConfig):
    """Test a balsamic case with no WGS sample that is not genotype compatible"""
    # GIVEN a balsamic case with a normal sample but no WGS tag
    case_obj = balsamic_context.status_db.

    # WHEN checking if genotype upload compatible
    genotype_check = case_obj.genotype_check

    # THEN
    assert genotype_check == False


def test_genotype_check_only_tumour(balsamic_context: CGConfig):
    """Test a balsamic case with only a tumour sample that is not genotype compatible"""
    # GIVEN a balsamic case with only tumour sample
    case_obj = balsamic_context.status_db.

    # WHEN checking if genotype upload compatible
    genotype_check = case_obj.genotype_check

    # THEN
    assert genotype_check == False
