# -*- coding: utf-8 -*-
import logging

import click
from dateutil.parser import parse as parse_date

from .api import QueueApi

log = logging.getLogger(__name__)


@click.group()
@click.option('-d', '--database', type=click.Path(), help='path to database')
@click.pass_context
def queue(context, database):
    """Interface to analysis queue."""
    database = database or context.obj['queue']['database']
    api = QueueApi(database)
    api.connect()
    context.obj = dict(api=api)


@queue.command()
@click.pass_context
def init(context):
    """Setup the database."""
    context.obj['api'].db.create_all()


@queue.command()
@click.option('-a', '--last-analyzed', help='last analysis date')
@click.option('-p', '--prioritize', is_flag=True, help='prioritize case')
@click.argument('case_id')
@click.pass_context
def add(context, case_id, last_analyzed=None, prioritize=None):
    """Add a new case to be analyzed."""
    old_case = context.obj['api'].case(case_id)
    if old_case:
        click.echo("case already exists: {}".format(old_case['case_id']))
    else:
        last_analyzed_at = parse_date(last_analyzed) if last_analyzed else None
        new_case = dict(case_id=case_id, last_analyzed_at=last_analyzed_at,
                        is_prioritized=prioritize)
        case_obj = context.obj['api'].save_case(new_case)
        click.echo("new case created: {case.case_id} ({case.id})".format(case=case_obj))


@queue.command()
@click.option('-l', '--limit', default=20, help='how many cases to display')
@click.pass_context
def cases(context, limit):
    """List cases in order of higest priority."""
    all_cases = context.obj['api'].cases()
    ready_cases = (case_obj for case_obj in all_cases if case_obj.is_ready())
    for index, case_obj in enumerate(ready_cases):
        if index > limit:
            break

        click.echo(case_obj.case_id)
