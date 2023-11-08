"""Common CLI file generation functions"""

import click

from cg.cli.generate.report.base import (
    generate_available_delivery_reports,
    generate_delivery_report,
)


@click.group()
def generate():
    """Generates and/or modifies files."""


generate.add_command(generate_delivery_report)
generate.add_command(generate_available_delivery_reports)
