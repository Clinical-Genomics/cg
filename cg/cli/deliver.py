# -*- coding: utf-8 -*- import logging

import os

import click
import logging
from pathlib import Path

from cg.store import Store
from cg.meta.deliver.api import DeliverAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deliver(context):
    """Deliver stuff."""
    pass

@deliver.command()
@click.option('-d', '--dry', is_flag=True, help='print config to console')
@click.option('-V', '--version', help='version (date) of bundle')
@click.option('-t', '--tag', multiple=True, help='the housekeeper tag(s)')
@click.option('-i', '--inbox', default='/mnt/hds/proj/{customer}/INBOX/{family}/', help='customer inbox')
@click.argument('family')
@click.pass_context
def inbox(context, dry, family, version, tag, inbox):
    """Link files from HK to cust inbox."""

    deliver_api = DeliverAPI(context.obj)
    db = Store(context.obj['database'])

    family_files = deliver_api.get_post_analysis_family_files(family=family, version=version, tag=tag)
    link_obj = db.family_samples(family)

    family_obj = db.family(family)
    for file_obj in family_files:
        out_path = Path(inbox.format(family=family_obj.name, customer=family_obj.customer.internal_id))

        #file_name = Path('_'.join([ tag.name for tag in file_obj.tags ]))
        #file_ext = ''.join(Path(file_obj.path).suffixes)
        file_name = Path(file_obj.path).name.replace(family, family_obj.name)
        new_path = f"{out_path / file_name}"

        os.link(file_obj.full_path, new_path)
        LOG.info(f"linked file: {file_obj.full_path} -> {new_path}")

    sample_files = {}
    for family_sample in link_obj:
        sample_obj = family_sample.sample
        sample_files = deliver_api.get_post_analysis_sample_files(family=family, sample=sample_obj.internal_id, version=version, tag=tag)

        for file_obj in sample_files:
            out_path = Path(inbox.format(family=family_obj.name, customer=family_obj.customer.internal_id))
            out_path = out_path.joinpath(sample_obj.name)

            file_name = Path(file_obj.path).name.replace(sample_obj.internal_id, sample_obj.name)
            new_path = f"{out_path / file_name}"

            os.link(file_obj.full_path, new_path)
            LOG.info(f"linked file: {file_obj.full_path} -> {new_path}")

