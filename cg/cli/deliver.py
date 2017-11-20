# -*- coding: utf-8 -*- import logging

import click
import logging
from pathlib import Path

from cg.apps import tb, hk, lims
from cg.store import Store

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
    status_api = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)

    family_obj = status_api.family(family)
    if family_obj is None:
        print(f"Family '{family}' not found.")
        context.abort()

    if not version:
        last_version = hk_api.last_version(bundle=family)
    else:
        last_version = hk_api.version(bundle=family, date=version)
    files = hk_api.files(bundle=family, version=last_version.id, tags=tag).all()

    for file_obj in files:
        out_path = Path(inbox.format(family=family_obj.name, customer=family_obj.customer.internal_id))
        file_name = Path('_'.join([ tag.name for tag in file_obj.tags ]))
        file_ext = ''.join(Path(file_obj.path).suffixes)
        new_path = f"{out_path / file_name}{file_ext}"

        os.link(file.full_path, new_path)
        LOG.info(f"linked file: {file_obj.full_path} -> {new_path}")

