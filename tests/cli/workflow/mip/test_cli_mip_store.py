"""This script tests the cli mip store functions"""
import logging

from cg.cli.workflow.mip.store import analysis, completed


def test_store_completed(cli_runner, mip_store_context, caplog):
    """Test if store completed stores function"""
    with caplog.at_level(INFO):
        result = cli_runner.invoke(completed, obj=mip_store_context)
        assert result.exit_code == 1
        assert ()


def test_store_completed(cli_runner, mip_configs: dict, mip_store_context, caplog):
    """Test if store completed stores a completed sample"""

    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(analysis, [str(mip_configs['yellowhog'])], obj=mip_store_context)
        assert result.exit_code == 0
        assert (
            "analysis stored: yellowhog"
            "included files in Housekeeper" in caplog.text
        )