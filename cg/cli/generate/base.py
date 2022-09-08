"""Common CLI file generation functions"""

import click

from cg.cli.generate.report.base import delivery_report, available_delivery_reports


@click.group()
def generate():
    """Generates and/or modifies files."""


generate.add_command(delivery_report)
generate.add_command(available_delivery_reports)
