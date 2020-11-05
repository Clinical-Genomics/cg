"""Test the upload genotype command"""

import logging

from click.testing import CliRunner

from cg.cli.upload.genotype import genotypes as upload_genotypes_cmd


def test_upload_genotype(
    upload_genotypes_context: dict, case_id: str, cli_runner: CliRunner, caplog
):
    """Test to upload genotypes via the CLI"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case that is ready for upload sequence genotypes
    family_obj = upload_genotypes_context["status_db"].family(case_id)
    assert family_obj

    # WHEN uploading the genotypes
    result = cli_runner.invoke(upload_genotypes_cmd, [case_id], obj=upload_genotypes_context)
    # THEN check that the command exits with success
    assert result.exit_code == 0
    # THEN assert the correct information is communicated
    assert "loading VCF genotypes for sample(s):" in caplog.text
