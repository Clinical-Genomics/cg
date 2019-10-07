""" Test the CLI for analysis rna """
import logging

from cg.cli.miprdrna import start
from cg.store import Store
from cg.apps.mip import MipAPI


def test_start_dry(cli_runner, tb_api, mock_store, caplog):
    """Test starting MIP"""
    # GIVEN a cli function

    context = {}
    context['db'] = mock_store
    context['tb_api'] = tb_api
    context['rna_api'] = MipAPI('${HOME}/bin/mip', 'analyse rd_rna')
    context['mip-rd-rna'] = {'mip_config': 'config.yaml'}

    # WHEN we start a case in dry run
    caplog.set_level(logging.INFO) 
    result = cli_runner.invoke(start, ['--dry', '--email', 'james.holden@scilifelab.se', 'angrybird'], obj=context)

    # THEN the command should be printed 
    with caplog.at_level(logging.INFO): 
        assert '${HOME}/bin/mip analyse rd_rna angrybird --config_file config.yaml --email james.holden@scilifelab.se --dry_run_all' in caplog.text 
