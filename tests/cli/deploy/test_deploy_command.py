"""Tests for running the deploy command"""

import logging
from pathlib import Path

from cg.cli.deploy.base import deploy
from cg.models.cg_config import CGConfig, CommonAppConfig
from click.testing import CliRunner


def test_running_deploy_fluffy(shipping_context: CGConfig, fluffy_config: Path, caplog):
    """Test to deploy fluffy with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    shipping_context.fluffy = CommonAppConfig(binary_path="echo", deploy_config=str(fluffy_config))
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy fluffy command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "fluffy"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_genotype(shipping_context: CGConfig, caplog):
    """Test to deploy genotype with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy genotype command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "genotype"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_hermes(shipping_context: CGConfig, hermes_config: Path, caplog):
    """Test to deploy hermes with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    shipping_context.hermes = CommonAppConfig(binary_path="echo", deploy_config=str(hermes_config))
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy hermes command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "hermes"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_loqusdb(shipping_context: CGConfig, caplog):
    """Test to deploy loqusdb with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy loqusdb command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "loqusdb"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_scout(shipping_context: CGConfig, scout_config: Path, caplog):
    """Test to deploy scout with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    shipping_context.scout = CommonAppConfig(binary_path="echo", deploy_config=str(scout_config))
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy scout command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "scout"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0


def test_running_deploy_shipping(shipping_context: CGConfig, base_context: CGConfig, caplog):
    """Test to deploy shipping with CG"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with some shipping configs

    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running the deploy shipping command in dry run mode
    result = runner.invoke(deploy, ["--dry-run", "shipping"], obj=shipping_context)

    # THEN assert that the command exits without problems
    assert result.exit_code == 0
