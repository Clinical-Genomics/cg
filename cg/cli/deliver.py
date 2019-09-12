# -*- coding: utf-8 -*- import logging

import logging
import os
from pathlib import Path

import click
from cg.apps import hk, lims
from cg.meta.deliver.api import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deliver(context):
    """Deliver stuff."""
    pass


@deliver.command()
@click.option('-V', '--version', help='version (date) of bundle')
@click.option('-t', '--tag', multiple=True, help='the housekeeper tag(s)')
@click.option('-i', '--inbox', 'inbox_path',
              default='/home/proj/production/customers/{customer}/inbox/{family}/',
              help='customer inbox')
@click.argument('family', required=False)
@click.pass_context
def inbox(context, family, version, tag, inbox_path):
    """Link files from HK to cust inbox."""

    db = Store(context.obj['database'])
    deliver_api = DeliverAPI(
        db=db,
        hk_api=hk.HousekeeperAPI(context.obj),
        lims_api=lims.LimsAPI(context.obj)
    )

    if not family:
        _suggest_cases_to_deliver(db)
        context.abort()

    family_obj = db.family(family)
    if family_obj is None:
        LOG.error(f"Case '{family}' not found.")
        context.abort()

    family_files = deliver_api.get_post_analysis_family_files(family=family, version=version,
                                                              tags=tag)
    if not family_files:
        LOG.warning(f"No case files found.")

    for file_obj in family_files:
        out_dir = Path(
            inbox_path.format(family=family_obj.name, customer=family_obj.customer.internal_id))
        out_dir.mkdir(parents=True, exist_ok=True)

        # might be fun to name exit files according to tags instead of MIP's long name
        # file_name = Path('_'.join([ tag.name for tag in file_obj.tags ]))
        # file_ext = ''.join(Path(file_obj.path).suffixes)
        out_file_name = Path(file_obj.path).name.replace(family, family_obj.name)
        out_path = Path(f"{out_dir / out_file_name}")
        in_path = Path(file_obj.full_path)

        if not out_path.exists():
            os.link(in_path, out_path)
            LOG.info(f"linked file: {in_path} -> {out_path}")
        else:
            LOG.info(f"Target file exists: {out_path}")

    link_obj = db.family_samples(family)
    if not link_obj:
        LOG.warning(f"No sample files found.")

    for family_sample in link_obj:
        sample_obj = family_sample.sample
        sample_files = deliver_api.get_post_analysis_sample_files(family=family,
                                                                  sample=sample_obj.internal_id,
                                                                  version=version, tag=tag)

        if not sample_files:
            LOG.warning(f"No sample files found for '{sample_obj.internal_id}'.")

        for file_obj in sample_files:
            out_dir = Path(
                inbox_path.format(family=family_obj.name, customer=family_obj.customer.internal_id))
            out_dir = out_dir.joinpath(sample_obj.name)
            out_dir.mkdir(parents=True, exist_ok=True)

            out_file_name = Path(file_obj.path).name.replace(sample_obj.internal_id,
                                                             sample_obj.name)
            out_path = Path(f"{out_dir / out_file_name}")
            in_path = Path(file_obj.full_path)

            if not out_path.exists():
                os.link(in_path, out_path)
                LOG.info(f"linked file: {in_path} -> {out_path}")
            else:
                LOG.info(f"Target file exists: {out_path}")


def _suggest_cases_to_deliver(store):
    LOG.info('provide a case, suggestions:')

    for family_obj in store.analyses_to_deliver()[:50]:
        click.echo(family_obj)
