# -*- coding: utf-8 -*-
import click

from cg import apps


def parse_caseid(raw_caseid):
    """Parse out parts of the case id."""
    customer_id, raw_familyid = raw_caseid.split('-', 1)
    case_id = raw_caseid.split('--')[0]
    family_parts = raw_familyid.split('--')
    family_id = family_parts[0]
    extra = family_parts[1] if len(family_parts) > 1 else None
    return {
        'raw': {
            'case_id': raw_caseid,
            'family_id': raw_familyid,
        },
        'customer_id': customer_id,
        'family_id': family_id,
        'case_id': case_id,
        'extra': extra,
    }


def check_latest_run(hk_db, context, case_info):
    # get latest analysis for the case
    latest_run = apps.hk.latest_run(hk_db, case_info['raw']['case_id'])
    if latest_run is None:
        click.echo("No run found for the case!")
        context.abort()
    return latest_run
