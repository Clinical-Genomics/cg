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


@pytest.fixture
def case_data_path():
    _in_data_path = 'tests/fixtures/cli/report/case_data.json'
    return _in_data_path


@pytest.fixture
def case_data(case_data_path):
    return json.load(open(case_data_path))
