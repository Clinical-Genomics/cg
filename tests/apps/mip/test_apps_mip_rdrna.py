""" Test MIP rare disease RNA app functionality """


def test_build_command(rna_api):
    """ Test building a command """
    # GIVEN just a config
    mip_config = 'tests/fixtures/global_config.yaml'
    case_id = 'angrybird'
    # WHEN building the MIP command
    mip_command = rna_api.build_command(case=case_id, config=mip_config)
    # THEN it should use the correct options
    assert mip_command == [rna_api.script, rna_api.pipeline, case_id, '--config_file', mip_config]
