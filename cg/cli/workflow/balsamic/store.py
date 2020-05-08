"""Click commands to store balsamic analyses"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import click

from cg.apps import hk
from cg.exc import CgError, StoreError
from cg.meta.store.balsamic import gather_files_and_bundle_in_housekeeper
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store
from cg.utils import fastq

LOG = logging.getLogger(__name__)
SUCCESS = 0
FAIL = 1


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["hk_api"] = hk.HousekeeperAPI(context.obj)
    context.obj["analysis_api"] = AnalysisAPI(
        db=Store(context.obj["database"]),
        hk_api=hk.HousekeeperAPI(context.obj),
        fastq_api=fastq.FastqAPI,
    )


@store.command()
@click.argument("case_id")
@click.option("-c", "--config", "config_path", required=False, help="Optional")
@click.option(
    "-c",
    "--config",
    "config_path",
    required=False,
    help="Path to case config file (json) generated by BALSAMIC ",
)
@click.option(
    "-d",
    "--deliverables-file",
    "deliverables_file_path",
    required=False,
    help="Path to deliverable file (*.hk) generated by BALSAMIC. ",
)
@click.pass_context
def analysis(context, case_id, deliverables_file_path, config_path):
    """Store a finished analysis in Housekeeper."""

    status = context.obj["db"]
    case_obj = status.family(case_id)
    root_dir = Path(context.obj["balsamic"]["root"])
    analysis_api = context.obj["analysis_api"]

    if not case_obj:
        raise CgError(f"Case {case_id} not found")

    if not deliverables_file_path:
        deliverables_file_path = analysis_api.get_deliverables_file_path(
            case_id, root_dir
        )
        if not os.path.isfile(deliverables_file_path):
            context.invoke(generate_deliverables_file, case_id=case_id)

    if not config_path:
        config_path = get_config_path(root_dir, case_id)

    hk_api = context.obj["hk_api"]

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_path, deliverables_file_path, hk_api, status, case_obj
        )
    except Exception:
        hk_api.rollback()
        status.rollback()
        raise StoreError(sys.exc_info()[0])

    status.add_commit(new_analysis)
    LOG.info("Included files in Housekeeper")


@store.command("all-cases")
@click.pass_context
def all_cases(context):

    _store = context.obj["db"]

    for case in _store.families():
        try:
            click.echo(click.style(f"storing case: {case}", fg="blue"))
            context.invoke(analysis, case_id=case.internal_id)
        except CgError as error:
            LOG.error(error.message)
            exit_code = 1

    sys.exit(exit_code)


@store.command("generate-deliverables-file")
@click.option("-d", "--dry-run", "dry", is_flag=True, help="print command to console")
@click.option("-c", "--config", "config_path", required=False, help="Optional")
@click.argument("case_id")
@click.pass_context
def generate_deliverables_file(context, dry, config_path, case_id):
    """Generate a deliverables file for the case_id."""

    conda_env = context.obj["balsamic"]["conda_env"]
    root_dir = Path(context.obj["balsamic"]["root"])
    case_obj = context.obj["db"].family(case_id)

    if not case_obj:
        raise CgError(f"Case {case_id} not found")

    if not config_path:
        config_path = analysis_api.get_config_path(root_dir, case_id)
        if not config_path.is_file():
            raise FileNotFoundError(
                f"Missing the sample-config file for {case_id}: {config_path}"
            )

    command_str = f" report deliver" f" --sample-config {config_path}'"
    command = [f"bash -c 'source activate {conda_env}; balsamic"]
    command.extend(command_str.split(" "))

    if dry:
        click.echo(" ".join(command))
        return SUCCESS

    process = subprocess.run(" ".join(command), shell=True)

    if process == SUCCESS:
        LOG.info("Created deliverables file")

    return process


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    _store = context.obj["db"]

    exit_code = SUCCESS
    for case in _store.cases_to_balsamic_analyze(limit=None):
        click.echo(click.style(f"Storing case: {case}", fg="blue"))
        try:
            exit_code = context.invoke(analysis, case_id=case.internal_id) and exit_code
        except StoreError as error:
            LOG.warning("Analysis could not be stored: %s", error.message)
            exit_code = FAIL

    click.echo(click.style(f"Done storing cases. Exit code: {exit_code}", fg="blue"))

    sys.exit(exit_code)


def get_config_path(root_dir, case_id):
    return Path.joinpath(root_dir, case_id, case_id + ".json")
