import logging

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import DRY_RUN
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def clean():
    """Clean up processes."""
    return


@clean.command("retrieve-spring-file")
@click.argument("spring-file-path", type=click.Path())
@DRY_RUN
@click.pass_obj
def update_archiving_status(config: CGConfig):
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    ddn_dataflow_api: DDNDataFlowApi = DDNDataFlowApi(config.ddn)
    for archiving_task in housekeeper_api.finished_tasks_to_update():
        if ddn_dataflow_api.is_task_completed(archiving_task):
            housekeeper_api.mark_files_as_archived(archiving_task=archiving_task)
            continue
        LOG.info(f"Task {archiving_task} exited with the code XXX")  # TODO fix logging
