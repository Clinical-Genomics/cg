"""Code that handles uploading to mutacc from the CLI"""

import logging

import rich_click as click

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.upload.utils import get_scout_api
from cg.constants.cli_options import DRY_RUN
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command("process-solved")
@click.option("-c", "--case-id", help="internal case id, leave empty to process all")
@click.option("-d", "--days-ago", type=int, default=1, help="days since solved")
@click.option("-C", "--customers", type=str, multiple=True, help="Filter on customers")
@DRY_RUN
@click.pass_obj
def process_solved(
    context: CGConfig, case_id: str | None, days_ago: int, customers: tuple[str], dry_run: bool
):
    """Process cases with mutacc that has been marked as solved in scout.
    This prepares them to be uploaded to the mutacc database"""

    LOG.info("----------------- PROCESS-SOLVED ----------------")

    scout_api: ScoutAPI = get_scout_api(cg_config=context, case_id=case_id)
    mutacc_auto_api: MutaccAutoAPI = context.mutacc_auto_api
    mutacc_upload_api = UploadToMutaccAPI(scout_api=scout_api, mutacc_auto_api=mutacc_auto_api)

    # Get cases to upload into mutacc from scout
    finished_cases: list[ScoutExportCase] = []
    if case_id is not None:
        finished_cases = scout_api.get_cases(finished=True, case_id=case_id)
    elif days_ago is not None:
        finished_cases = scout_api.get_solved_cases(days_ago=days_ago)
    else:
        LOG.info("Please enter option '--case-id' or '--days-ago'")

    number_processed = 0
    for case in finished_cases:
        number_processed += 1
        if customers and case.owner not in customers:
            LOG.info(f"skipping {case.id}: Not valid customer {case.owner}")
            continue
        if dry_run:
            LOG.info(f"Would process case {case.id} with mutacc")
            continue

        LOG.info(f"Start processing case {case.id} with mutacc")
        mutacc_upload_api.extract_reads(case)

    if number_processed == 0:
        LOG.info(f"No cases were solved within the last {days_ago} days")


@click.command("processed-solved")
@click.pass_obj
def processed_solved(context: CGConfig):
    """Upload solved cases that has been processed by mutacc to the mutacc database"""

    mutacc_auto_api: MutaccAutoAPI = context.mutacc_auto_api

    LOG.info("----------------- PROCESSED-SOLVED ----------------")

    LOG.info("Uploading processed cases by mutacc to the mutacc database")

    mutacc_auto_api.import_reads()
