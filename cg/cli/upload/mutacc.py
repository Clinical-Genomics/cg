"""Code that handles uploading to mutacc from the CLI"""
import logging

import click

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.meta.upload.mutacc import UploadToMutaccAPI

LOG = logging.getLogger(__name__)


@click.command("process-solved")
@click.option("-c", "--case-id", help="internal case id, leave empty to process all")
@click.option("-d", "--days-ago", type=int, default=1, help="days since solved")
@click.option("-C", "--customers", type=str, multiple=True, help="Filter on customers")
@click.option("--dry-run", is_flag=True, help="only print cases to be processed")
@click.pass_context
def process_solved(context, case_id, days_ago, customers, dry_run):
    """Process cases with mutacc that has been marked as solved in scout.
    This prepares them to be uploaded to the mutacc database"""

    click.echo(click.style("----------------- PROCESS-SOLVED ----------------"))

    scout_api = context.obj["scout_api"]
    mutacc_auto_api = MutaccAutoAPI(context.obj)

    mutacc_upload = UploadToMutaccAPI(scout_api=scout_api, mutacc_auto_api=mutacc_auto_api)

    # Get cases to upload into mutacc from scout
    if case_id is not None:
        finished_cases = scout_api.get_cases(finished=True, case_id=case_id)
    elif days_ago is not None:
        finished_cases = scout_api.get_solved_cases(days_ago=days_ago)
    else:
        LOG.info("Please enter option '--case-id' or '--days-ago'")

    number_processed = 0
    for case in finished_cases:

        number_processed += 1
        if customers:
            if case["owner"] not in customers:
                LOG.info("skipping %s: Not valid customer %s", case["_id"], case["owner"])
                continue
        if dry_run:
            LOG.info("Would process case %s with mutacc", case["_id"])
            continue

        LOG.info("Start processing case %s with mutacc", case["_id"])
        mutacc_upload.extract_reads(case)

    if number_processed == 0:
        LOG.info("No cases were solved within the last %s days", days_ago)


@click.command("processed-solved")
@click.pass_context
def processed_solved(context):
    """Upload solved cases that has been processed by mutacc to the mutacc database"""

    click.echo(click.style("----------------- PROCESSED-SOLVED ----------------"))

    LOG.info("Uploading processed cases by mutacc to the mutacc database")

    mutacc_auto_api = MutaccAutoAPI(context.obj)
    mutacc_auto_api.import_reads()
