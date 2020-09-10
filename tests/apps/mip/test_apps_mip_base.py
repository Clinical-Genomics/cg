""" Test MIP app functionality """

from subprocess import CalledProcessError

import pytest

from cg.constants import SINGLE_QUOTE, SPACE


def test_build_command(mip_api, mip_config_path, case_id):
    """ Test building a command """
    # GIVEN a config

    # WHEN building the MIP command
    mip_command = mip_api.build_command(case=case_id, config=mip_config_path)
    expected_binary_command = [mip_api.script, mip_api.pipeline, case_id]

    # THEN it should use the correct options
    assert mip_command == {
        "binary": SPACE.join(expected_binary_command),
        "environment": mip_api.conda_env,
        "config": mip_config_path,
        "parameters": [],
    }


def test_execute_when_dry_run(mip_api, mip_config_path: str, case_id: str):
    """Test executing a command"""
    ## GIVEN a config and a build command
    build_command = mip_api.build_command(case=case_id, config=mip_config_path)

    ## WHEN executing in dry run mode
    return_code = mip_api.execute(build_command, dry_run=True)

    ## THEN return success
    assert return_code == 0
