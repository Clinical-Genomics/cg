"""Common CLI file generation functions"""

import click

from cg.cli.generate.report.base import (
    generate_available_delivery_reports,
    generate_delivery_report,
)
from cg.cli.utils import click_context_setting_max_content_width


@click.group(context_settings=click_context_setting_max_content_width())
def generate():
    """Generates and/or modifies files."""


generate.add_command(generate_delivery_report)
generate.add_command(generate_available_delivery_reports)
