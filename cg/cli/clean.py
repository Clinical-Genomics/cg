# -*- coding: utf-8 -*-
import logging

import ruamel.yaml
import click
from dateutil.parser import parse as parse_date

from cg.apps import tb, hk
from cg.store import Store

LOG = logging.getLogger(__name__)

@click.group()
@click.pass_context
def clean(context):
    """Remove stuff."""
    context.obj['db'] = Store(context.obj['database'])
    context.obj['tb'] = tb.TrailblazerAPI(context.obj)


@clean.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('-y', '--yes', is_flag=True, help='skip confirmation')
@click.argument('sample_info', type=click.File('r'))
@click.pass_context
def mip(context, dry, yes, sample_info):
    """Remove analysis output."""
    raw_data = ruamel.yaml.safe_load(sample_info)
    data = context.obj['tb'].parse_sampleinfo(raw_data)

    family = data['family']
    family_obj = context.obj['db'].family(family)
    if family_obj is None:
        print(f"Family '{family}' not found.")
        context.abort()

    analysis_obj = context.obj['db'].analysis(family_obj, data['date'])
    if analysis_obj is None:
        print(f"{family}: {data['date']} not found")
        context.abort()
    elif analysis_obj.is_deleted:
        print(click.style(f"{family}: analysis already deleted", fg='red'))
        context.abort()

    try:
        context.obj['tb'].delete_analysis(family, data['date'], yes=yes)
    except ValueError as error:
        print(click.style(f"{family}: {error.args[0]}"))
        context.abort()


@clean.command()
@click.option('-y', '--yes', is_flag=True, help='skip confirmation')
@click.argument('before_str')
@click.pass_context
def auto(context: click.Context, before_str: str, yes: bool=False):
    """Automatically clean up "old" analyses."""
    before = parse_date(before_str)
    old_analyses = context.obj['db'].analyses(before=before)
    for status_analysis in old_analyses:
        family_id = status_analysis.family.internal_id
        tb_analysis = context.obj['tb'].find_analysis(family_id, status_analysis.started_at)

        if tb_analysis is None:
            print(click.style(f"{family_id}: analysis not found in Trailblazer", fg='yellow'))
            continue
        elif tb_analysis.is_deleted:
            print(click.style(f"{family_id}: analysis already deleted", fg='yellow'))
            continue
        elif context.obj['tb'].analyses(family=family_id, temp=True).count() > 0:
            print(click.style(f"{family_id}: family already re-started", fg='yellow'))
            continue

        print(click.style(f"{family_id}: cleaning MIP output", fg='blue'))
        sampleinfo_path = context.obj['tb'].get_sampleinfo(tb_analysis)
        context.invoke(mip, yes=yes, sample_info=sampleinfo_path)
