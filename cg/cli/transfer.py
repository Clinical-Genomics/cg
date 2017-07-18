# -*- coding: utf-8 -*-
import logging

from cgadmin.store.api import AdminDatabase
from housekeeper.store import api as hk_api
import click

from cg.apps import lims, scoutapi, transfer as transfer_app
from cg.store import Store

log = logging.getLogger(__name__)


@click.command()
@click.pass_context
def transfer(context):
    """Transfer stuff from external interfaces."""
    status_api = Store(context.obj['database'])
    admin_api = AdminDatabase(context.obj['cgadmin']['database'])
    log.info('loading customers')
    customer_importer = transfer_app.CustomerImporter(status_api, admin_api)
    customer_importer.records()

    log.info('loading users')
    user_importer = transfer_app.UserImporter(status_api, admin_api)
    user_importer.records()

    log.info('loading applications')
    application_importer = transfer_app.ApplicationImporter(status_api, admin_api)
    application_importer.records()

    log.info('loading application versions')
    version_importer = transfer_app.VersionImporter(status_api, admin_api)
    version_importer.records()

    scout_api = scoutapi.ScoutAPI(context.obj)
    log.info('loading panels')
    panel_importer = transfer_app.PanelImporter(status_api, scout_api)
    panel_importer.records()

    lims_api = lims.LimsAPI(context.obj)
    log.info('loading samples, families, and links')
    sample_importer = transfer_app.SampleImporter(status_api, lims_api)
    sample_importer.records()

    hk_manager = hk_api.manager(context.obj['housekeeper']['old']['database'])
    log.info('loading analyses')
    analysis_importer = transfer_app.AnalysisImporter(status_api, hk_manager)
    analysis_importer.records()
