# -*- coding: utf-8 -*-
import logging
import sys
import json
import click

from cg.apps import tb, hk, lims
from cg.store import Store
from cg.meta.report.api import ReportAPI

LOG = logging.getLogger(__name__)


def validate_stdin(context, param, value):
    """Validate piped input contains some data.

    Raises:
        click.BadParameter: if STDIN is empty
    """
    # check if input is a file or stdin
    if value.name == '<stdin>' and sys.stdin.isatty():  # pragma: no cover
        # raise error if stdin is empty
        raise click.BadParameter('you need to pipe something to stdin')
    return value


@click.group()
@click.pass_context
def report(context):
    """Create Reports"""
    context.obj['db'] = Store(context.obj['database'])


@report.command()
@click.argument('in_data', callback=validate_stdin,
                type=click.File(encoding='utf-8', mode='r'), default='-', required=False)
@click.pass_context
def qc(context, in_data):
    """Generate a QC report for a case."""

    case_data = json.load(in_data)
    db = context.obj['db']
    report_api = ReportAPI(
        db=db,
        hk_api=hk.HousekeeperAPI(context.obj),
        lims_api=lims.LimsAPI(context.obj)
    )

    qc_data = report_api.generate_qc_data(db, case_data)
    template_out = report_api.render_qc_report(qc_data)
    click.echo(template_out)


