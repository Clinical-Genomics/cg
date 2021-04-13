"""CLI for delivering files with CG"""
import copy
import logging
from pathlib import Path
from typing import List

import click
import subprocess

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS, PIPELINE_ANALYSIS_TAG_MAP
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deliver(context):
    """Deliver files with CG."""
    LOG.info("Running CG deliver")
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)


@click.command(name="analysis")
@click.option("-c", "--case-id", help="Deliver the files for a specific case")
@click.option(
    "-t", "--ticket-id", type=int, help="Deliver the files for ALL cases connected to a ticket"
)
@click.option("-d", "--delivery-type", type=click.Choice(PIPELINE_ANALYSIS_OPTIONS), required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deliver_analysis(context, case_id: str, ticket_id: int, delivery_type: str, dry_run: bool):
    """Deliver analysis files to customer inbox

    Files can be delivered either on case level or for all cases connected to a ticket.
    Any of those needs to be specified.
    """
    if not (case_id or ticket_id):
        LOG.info("Please provide a case-id or ticket-id")
        return

    inbox = context.obj.get("delivery_path")
    if not inbox:
        LOG.info("Please specify the root path for where files should be delivered")
        return

    status_db: Store = context.obj["status_db"]
    deliver_api = DeliverAPI(
        store=status_db,
        hk_api=context.obj["housekeeper_api"],
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
        project_base_path=Path(inbox),
        delivery_type=delivery_type,
    )
    deliver_api.set_dry_run(dry_run)
    if case_id:
        case_obj = status_db.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases = [case_obj]
    else:
        cases: List[Family] = status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find cases for ticket_id %s", ticket_id)
            return

    for case_obj in cases:
        deliver_api.deliver_files(case_obj=case_obj)


@click.command(name="old-analysis")
@click.option("-c", "--case-id", help="Deliver the files for a specific case")
@click.option(
    "-t", "--ticket-id", type=int, help="Deliver the files for ALL cases connected to a ticket"
)
@click.option("-d", "--delivery-type", type=click.Choice(PIPELINE_ANALYSIS_OPTIONS), required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deliver_old_analysis(context, case_id: str, ticket_id: int, delivery_type: str, dry_run: bool):
    """Deliver old analysis files to customer inbox

    Files can be delivered either on case level or for all cases connected to a ticket.
    Any of those needs to be specified.
    """

    BALSAMIC_ANALYSIS_ONLY_CASE_TAGS = [
        {"vcf-snv-clinical"},
        {"vcf-snv-clinical-index"},
        {"vcf-pass"},
        {"vcf-sv-clinical"},
        {"vcf-sv-clinical-index"},
        {"cnvkit", "visualization"},
        {"cnv-scatter", "scatter"},
        {"cnvkit", "visualization", "diagram"},
        {"cnv-diagram", "diagram"},
        {"cnr"},
        {"multiqc-html"},
    ]

    BALSAMIC_ANALYSIS_CASE_TAGS = copy.deepcopy(BALSAMIC_ANALYSIS_ONLY_CASE_TAGS)
    BALSAMIC_ANALYSIS_CASE_TAGS.extend(
        [
            {"cram", "normal"},
            {"cram-index"},
            {"cram", "tumor"},
            {"cram-index", "tumor"},
            {"cram", "tumor-cram"},
            {"cram", "tumor-cram-index"},
            {"cram", "normal-cram"},
            {"cram", "normal-cram-index"},
        ]
    )

    BALSAMIC_ANALYSIS_SAMPLE_TAGS = [
        {"cram", "normal"},
        {"cram-index"},
        {"cram", "tumor"},
        {"cram-index", "tumor"},
        {"bam"},
        {"bam-index"},
        {"bam", "tumor-bam"},
        {"bam", "tumor-bam-index"},
        {"bam", "normal-bam"},
        {"bam", "normal-bam-index"},
        {"cram", "tumor-cram"},
        {"cram", "tumor-cram-index"},
        {"cram", "normal-cram"},
        {"cram", "normal-cram-index"},
    ]

    BALSAMIC_QC_CASE_TAGS = [
        {"multiqc-html"},
    ]
    BALSAMIC_QC_SAMPLE_TAGS = [{"fastq"}, {"read1"}, {"read2"}]

    OLD_PIPELINE_ANALYSIS_TAG_MAP = {
        "balsamic": {
            "case_tags": BALSAMIC_ANALYSIS_CASE_TAGS,
            "sample_tags": BALSAMIC_ANALYSIS_SAMPLE_TAGS,
        },
        "balsamic-analysis": {"case_tags": BALSAMIC_ANALYSIS_ONLY_CASE_TAGS, "sample_tags": []},
        "balsamic-qc": {
            "case_tags": BALSAMIC_QC_CASE_TAGS,
            "sample_tags": BALSAMIC_QC_SAMPLE_TAGS,
        },
    }
    if not (case_id or ticket_id):
        LOG.info("Please provide a case-id or ticket-id")
        return

    inbox = context.obj.get("delivery_path")
    if not inbox:
        LOG.info("Please specify the root path for where files should be delivered")
        return

    status_db: Store = context.obj["status_db"]
    deliver_api = DeliverAPI(
        store=status_db,
        hk_api=context.obj["housekeeper_api"],
        case_tags=OLD_PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
        sample_tags=OLD_PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
        project_base_path=Path(inbox),
        delivery_type=delivery_type,
    )
    deliver_api.set_dry_run(dry_run)
    if case_id:
        case_obj = status_db.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases = [case_obj]
    else:
        cases: List[Family] = status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find cases for ticket_id %s", ticket_id)
            return

    for case_obj in cases:
        deliver_api.deliver_files(case_obj=case_obj)


@click.command(name="rsync")
@click.option(
    "-t", "--ticket-id", type=int, help="Rsync the files for a specific ticket", required=True
)
@click.option("--dry-run", is_flag=True)
@click.option("--covid", is_flag=True)
@click.pass_context
def rsync(context, ticket_id: int, dry_run: bool, covid: bool):
    """The folder generated using the "cg deliver analysis" command will be
    rsynced with this function to the customers inbox on caesar.
    """
    paths = {
        "base_source_path": context.obj.get("delivery_path"),
        "destination_path": context.obj["data-delivery"]["destination_path"],
        "covid_destination_path": context.obj["data-delivery"]["covid_destination_path"],
        "covid_source_path": context.obj["data-delivery"]["covid_source_path"],
    }
    status_db = context.obj["status_db"]
    rsync_api = RsyncAPI(store=status_db)
    rsync_api.run_rsync_command(ticket_id=ticket_id, paths=paths, dry_run=dry_run)
    if covid:
        rsync_api.run_covid_rsync_command(ticket_id=ticket_id, paths=paths, dry_run=dry_run)


deliver.add_command(deliver_analysis)
deliver.add_command(deliver_old_analysis)
deliver.add_command(rsync)
