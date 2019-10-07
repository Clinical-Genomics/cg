""" Test the CLI for analysis rna """

from cg.cli.miprdrna import start
from cg.store import Store
from cg.apps.mip import MipAPI


class Config():
    """ Click context obj :)"""
    def __init__(self):
        """ """
        self.obj = {}


def test_start_dry(invoke_cli, tb_api):
    """Test starting MIP"""
    # GIVEN a cli function
    config = Config()
    config.obj['db'] = Store(config)
    config.obj['tb_api'] = tb_api()
    config.obj['rna_api'] = MipAPI('fake_mip', 'fake rna')

    # WHEN we start a case in dry run
    result = invoke_cli(start, ['--dry', '--email', 'fake.email@scilifelab.se'], obj=config)
    
    # THEN the command should be printed
    assert result == 'fake_mip fake rna'
