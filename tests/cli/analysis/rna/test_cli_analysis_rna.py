""" Test the CLI for analysis rna """

from collections import namedtuple

from cg.cli.miprdrna import start
from cg.store import Store
from cg.apps.mip import MipAPI


def test_start_dry(cli_runner, invoke_cli, tb_api, mock_store):
    """Test starting MIP"""
    # GIVEN a cli function
    import ipdb; ipdb.set_trace()

    config = namedtuple('Config', 'obj')
    config.obj = {}
    config.obj['db'] = mock_store
    config.obj['tb_api'] = tb_api
    config.obj['rna_api'] = MipAPI('fake_mip', 'fake rna')

    # WHEN we start a case in dry run
    #result = cli_runner.invoke(start, ['--dry', '--email', 'fake.email@scilifelab.se', 'angrybird'], obj=config)
    result = invoke_cli(['analysis', 'rna', 'start', '--dry', '--email', 'fake.email@scilifelab.se', 'angrybird'], obj=config)

    # THEN the command should be printed
    assert result.output == 'fake_mip fake rna'
