"""
    Test cases for Vogue load cli
"""
import logging

from cg.cli.workflow.mip_dna.store import _add_new_complete_analysis_record
from cg.store import Store

def test_upload_vogue_bioinfo_dry(invoke_cli, base_context):
    """
    Test dry run with minimal options
    """
    
    # GIVEN a dummy case name 
    case_name = base_context["status"].families().first().internal_id

    # WHEN trying to upload with a family that doesn't exist
    result = invoke_cli(["upload", "vogue", "bioinfo", "--case-name", case_name, "--dry"])

    # THEN it fails hard and reports that it is missing the family
    assert result.exit_code == 0

