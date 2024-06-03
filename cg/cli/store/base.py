"""Code for store part of CLI."""

import logging

import click

from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.utils import click_context_setting_max_content_width
from cg.meta.compress.compress import CompressAPI
from cg.models.cg_config import CGConfig

from .store import (
    store_case,
    store_demultiplexed_flow_cell,
    store_flow_cell,
    store_qc_metrics,
    store_sample,
    store_ticket,
)

LOG = logging.getLogger(__name__)


@click.group(context_settings=click_context_setting_max_content_width())
@click.pass_obj
def store(context: CGConfig):
    """Command for storing files."""
    LOG.info("Running CG store command")
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    crunchy_api: CrunchyAPI = context.crunchy_api

    compress_api = CompressAPI(
        hk_api=housekeeper_api,
        crunchy_api=crunchy_api,
        demux_root=context.illumina_flow_cells_directory,
    )
    context.meta_apis["compress_api"] = compress_api


for sub_cmd in [
    store_case,
    store_demultiplexed_flow_cell,
    store_flow_cell,
    store_sample,
    store_ticket,
    store_qc_metrics,
]:
    store.add_command(sub_cmd)
