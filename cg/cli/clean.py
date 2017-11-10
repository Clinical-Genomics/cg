# -*- coding: utf-8 -*-
import logging

import ruamel.yaml
import click

from cg.apps import tb, hk
from cg.store import Store

LOG = logging.getLogger(__name__)

@click.group()
@click.pass_context
def clean(context):
    """Remove stuff."""
    context.obj['db'] = Store(context.obj['database'])


@clean.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('-y', '--yes', is_flag=True, help='skip confirmation')
@click.argument('sample_info', type=click.File('r'))
@click.pass_context
def mip(context, dry, yes, sample_info):
    """Remove analysis output."""


    tb_api = tb.TrailblazerAPI(context.obj)
    
    raw_data = ruamel.yaml.safe_load(sample_info)
    data = tb_api.parse_sampleinfo(raw_data)

    family = data['family']
    family_obj = context.obj['db'].family(family)
    if family_obj is None:
        print(f"Family '{family}' not found.")
        context.abort()

    analysis_obj = context.obj['db'].analysis(family_obj, data['date'])
    if analysis_obj is None:
        print(f"{family}: {data['date']} not found") 
        context.abort()

    tb_api.delete_analysis(family, data['date'], yes=yes)
