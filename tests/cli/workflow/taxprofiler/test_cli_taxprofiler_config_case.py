"""Tests cli methods to create the case config for Taxprofiler."""

import logging
from pathlib import Path
from typing import List

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
