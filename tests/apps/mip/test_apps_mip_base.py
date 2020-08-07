""" Test MIP app functionality """

from cg.constants import SINGLE_QUOTE


def test_build_command(mip_api, mip_config_path, case_id):
    """ Test building a command """
    # GIVEN just a config
    # WHEN building the MIP command
    mip_command = mip_api.build_command(case=case_id, config=mip_config_path)
    # THEN it should use the correct options
    assert mip_command == [
        f"bash -c 'source activate {mip_api.conda_env};",
        mip_api.script,
        mip_api.pipeline,
        case_id,
        "--config_file",
        mip_config_path,
        SINGLE_QUOTE,
    ]
