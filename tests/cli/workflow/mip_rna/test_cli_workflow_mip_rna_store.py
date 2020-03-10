"""
Test the cli command `cg workflow mip-rna store`
This command is used to store mip-rna results in Housekeeper
"""
from cg.cli.workflow.mip_rna.store import analysis


SUCCESS = 0


# def test_func(cli_runner, rna_store_context, rna_config, deliverables):
# def test_func(cli_runner, tb_api, mock_store):
#     # GIVEN a file with deliverables from a MIP-RNA analysis
#     context = {}
#     context['db'] = mock_store
#     context['tb_api'] = tb_api


#     # WHEN running the command from the cli
#     result = cli_runner.invoke(analysis, obj=context)

#     # THEN
#     assert context['tb_api'] == 'tb_api'
#     assert result.exit_code == SUCCESS
#     assert result.output == []


# def test_add_analysis():
#     pass


# def test_parse_config():
#     pass


# def test_parse_sampleinfo():
#     pass


# def test_build_bundle():
#     pass


# def test_get_files():
#     pass


# def test_get_multiple_paths():
#     pass
