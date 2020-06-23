""" Add CLI support to create config and/or start BALSAMIC """
import gzip
import logging
import re
import subprocess
import sys
import shutil
import click
from cg.apps import hk, lims
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.workflow.base import get_target_bed_from_lims
from cg.store import Store
from cg.utils.commands import Process
from pathlib import Path
from cg.meta.workflow.balsamic import MetaBalsamicAPI, AnalysisAPI

LOG = logging.getLogger(__name__)


ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing"
)


@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context):
    """Initialize MetaBalsamicAPI"""
    context.obj["MetaBalsamicAPI"] = MetaBalsamicAPI(context.obj)


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context, case_id):
    """"Link samples to case ID"""

    LOG.info(f"Link all samples in case {case_id}")
    case_object = context.obj["MetaBalsamicAPI"].lookup_samples(case_id)
    if case_object:
        if case_object.links:
            context.obj["MetaBalsamicAPI"].link_samples(case_object.links)
        else:
            LOG.warning(f"{case_id} has no linked samples")
            click.Abort()
    else:
        LOG.warning(f"{case_id} is not present in database")
        click.Abort()


@balsamic.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("--panel-bed", required=False, help="Optional")
@click.pass_context
def config_case(context, panel_bed, case_id, dry):
    """Create config file for BALSAMIC analysis of a case"""

    LOG.info(f"Creating config for {case_id}")
    case_object = context.obj["MetaBalsamicAPI"].lookup_samples(case_id)
    if case_object:
        if case_object.links:
            arguments = {
                "case_id": case_id,
                "normal": "",
                "tumor": "",
                "panel_bed": "",
                "output_config": f"{case_id}.json",
            }

            acceptable_applications = {"wgs", "wes", "tgs"}
            applications_requiring_bed = {"wes", "tgs"}
            setup_data = context.obj["MetaBalsamicAPI"].get_case_config_params(
                case_id, case_object.links
            )

            # Can be handled with pandas eloquently in future
            normal_paths = [
                v["concatenated_path"]
                for k, v in setup_data.items()
                if v["tissue_type"] == "normal"
            ]
            tumor_paths = [
                v["concatenated_path"] for k, v in setup_data.items() if v["tissue_type"] == "tumor"
            ]
            application_types = set([v["application_type"] for k, v in setup_data.items()])
            target_beds = set([v["target_bed"] for k, v in setup_data.items()])

            # Check if normal samples are 1
            if len(normal_paths) == 1:
                arguments["normal"] = normal_paths[0]
            elif len(normal_paths) == 0:
                arguments["normal"] = None
            elif len(normal_paths) > 1:
                LOG.warning(f"Too many normal samples found: {len(normal_paths)}")
                click.Abort()

            # Check if tumor samples are 1
            if len(tumor_paths) == 1:
                arguments["tumor"] = normal_paths[0]
            elif len(tumor_paths) == 0:
                LOG.warning(f"No tumor samples found for {case_id}")
                click.Abort()
            elif len(tumor_paths) > 1:
                LOG.warning(f"Too many tumor samples found: {len(tumor_paths)}")
                click.Abort()

            # Check application type is only one
            if len(application_types) > 1:
                LOG.warning(f"More than one application found for case {case_id}")
                click.Abort()
            elif len(application_types) == 0:
                LOG.warning(f"No application found for case {case_id}")
                click.Abort()

            # Check if application type is suitable for BALSAMIC
            if application_types.issubset(acceptable_applications):
                LOG.info(f"Application type {application_types}")
            else:
                LOG.warning(f"Improper application type for case {case_id}")
                click.Abort()

            # If panel BED is provided, check if panel BED is compatible with application type
            if panel_bed:
                if application_types.issubset(applications_requiring_bed):
                    arguments["panel_bed"] = panel_bed
                else:
                    LOG.warning(f"Panel BED {panel_bed} incompatible with application type")
                    click.Abort()
            # If panel BED is not provided, it should be inferred.
            else:
                if application_types.issubset(applications_requiring_bed):
                    if len(target_beds) == 0:
                        LOG.warning(f"Panel BED cannot be found for sample {case_id}")
                        click.Abort()
                    elif len(target_beds) > 1:
                        LOG.warning(f"Multiple Panel BED indicated for sample {case_id}")
                        click.Abort()
                    else:
                        arguments["panel_bed"] = target_beds.pop()
                else:
                    arguments["panel_bed"] = None
        else:
            LOG.warning(f"{case_id} has no linked samples")
            click.Abort()
    else:
        LOG.warning(f"{case_id} is not present in database")
        click.Abort()

    context.obj["MetaBalsamicAPI"].balsamic_api.co


@balsamic.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
@click.option("-a", "--analysis-type", type=click.Choice(["qc", "paired", "single"]))
@click.option("-r", "--run-analysis", is_flag=True, default=False, help="Execute in non-dry mode")
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):

    arguments = {
        "priority": None,
        "analysis_type": None,
        "run_analysis": False,
        "case_id": case_id,
    }
    if priority:
        arguments["priority"] = priority
    if analysis_type:
        arguments["analysis_type"] = analysis_type
    if run_analysis:
        arguments["run_analysis"] = run_analysis

    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):
    """Remove stored FASTQ files"""

    work_dir = Path(f"{context.obj['balsamic']['root']}/{case_id}/fastq")
    if work_dir.exists():
        shutil.rmtree(work_dir)
        LOG.info(f"Path {work_dir} removed successfully")
    else:
        LOG.info(f"Path {work_dir} does not exist")


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def start(context, case_id):
    """Invoke all commands"""

    context.invoke(link)
    context.invoke(config_case)
    context.invoke(run)
    context.invoke(remove_fastq)
