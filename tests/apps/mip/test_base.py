""" Test MIP app functionality """


def test_build_command(mip_cli):
    """ Test building a command """
    # GIVEN just a config
    mip_config = 'tests/fixtures/global_config.yaml'
    case_id = 'angrybird'
    # WHEN building the MIP command
    mip_command = mip_cli.build_command(case=case_id, config=mip_config)
    # THEN it should use the correct options
    assert mip_command == [mip_cli.script, mip_cli.pipeline, case_id, '--config_file', mip_config]
