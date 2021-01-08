"""Tests for running the deploy command"""

import logging
from pathlib import Path
from typing import Dict
from cg.cli.deploy.base import deploy

from click.testing import CliRunner


def test_running_deploy_shipping(shipping_configs: Dict[str, str], caplog):
    """Test to deploy shipping with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs
    context = dict(shipping=shipping_configs)
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy shipping command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "shipping"], obj=context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_genotype(shipping_configs: Dict[str, str], caplog):
    """Test to deploy genotype with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs
    context = dict(shipping=shipping_configs)
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy genotype command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "genotype"], obj=context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_scout(shipping_configs: Dict[str, str], scout_config: Path, caplog):
    """Test to deploy scout with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs
    context = dict(shipping=shipping_configs)
    context["scout"] = dict(deploy_config=str(scout_config))
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy genotype command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "scout"], obj=context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0
