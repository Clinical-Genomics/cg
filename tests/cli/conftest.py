from functools import partial

from click.testing import CliRunner
import pytest
import json
from cg.cli import base


@pytest.fixture
def cli_runner():
    runner = CliRunner()
    return runner


@pytest.fixture
def invoke_cli(cli_runner):
    return partial(cli_runner.invoke, base)


