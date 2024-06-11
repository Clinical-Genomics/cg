"""Common CLI file generation functions"""

import click

from cg.cli.generate.report.base import (
    generate_available_delivery_reports,
    generate_delivery_report,
)
from cg.cli.utils import CLICK_CONTEXT_SETTINGS


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def generate():
    """Generates and/or modifies files."""


generate.add_command(generate_delivery_report)
generate.add_command(generate_available_delivery_reports)
