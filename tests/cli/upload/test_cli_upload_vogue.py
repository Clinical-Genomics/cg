"""
    Test cases for Vogue load cli
"""
import logging

def test_upload_vogue_bioinfo_dry(invoke_cli):
    """
    Test dry run with minimal options
    """
    
    # GIVEN a dummy case name 
    case_name = "dummy_case"

    # WHEN trying to upload with a family that doesn't exist
    result = invoke_cli(["upload", "vogue", "bioinfo", "--case-name", case_name, "--dry"])

    # THEN it fails hard and reports that it is missing the family
    assert result.exit_code != 0

