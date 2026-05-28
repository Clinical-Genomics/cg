"""Code for store part of CLI."""

import logging

import rich_click as click

from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.prepare.prepare import (
    prepare_case,
    prepare_demultiplexed_illumina_run,
    prepare_illumina_run,
    prepare_sample,
    prepare_ticket,
)
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.meta.compress.compress import CompressAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def prepare(context: CGConfig):
    """Command for preparing files for analysis."""
    LOG.info("Running CG prepare command")
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    crunchy_api: CrunchyAPI = context.crunchy_api

    compress_api = CompressAPI(
        hk_api=housekeeper_api,
        crunchy_api=crunchy_api,
        demux_root=context.run_instruments.illumina.sequencing_runs_dir,
    )
    context.meta_apis["compress_api"] = compress_api


for sub_cmd in [
    prepare_case,
    prepare_demultiplexed_illumina_run,
    prepare_illumina_run,
    prepare_sample,
    prepare_ticket,
]:
    prepare.add_command(sub_cmd)
