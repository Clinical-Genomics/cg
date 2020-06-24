""" Add CLI support to create config and/or start BALSAMIC """
import logging
import shutil
import click
from cg.apps import hk, lims
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.workflow.base import get_target_bed_from_lims
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import Store

LOG = logging.getLogger(__name__)
PRIORITY_OPTION = click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
EMAIL_OPTION = click.option("-e", "--email", help="email to send errors to")
ANALYSIS_TYPE_OPTION = click.option(
    "-a", "--analysis-type", type=click.Choice(["qc", "paired", "single"])
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing"
)


@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context):
    """Run BALSAMIC"""

    context.obj["MetaBalsamicAPI"] = MetaBalsamicAPI(context.obj)


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context, case_id, sample_id):
    """Link FASTQ files for a SAMPLE_ID."""
    store = context.obj["store_api"]
    link_objs = get_links(store, case_id, sample_id)

    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files", link_obj.sample.internal_id, link_obj.sample.data_analysis,
        )
        if link_obj.sample.data_analysis and "balsamic" in link_obj.sample.data_analysis.lower():
            LOG.info(
                "%s has balsamic as data analysis, linking.", link_obj.sample.internal_id,
            )
            context.obj["analysis_api"].link_sample(
                fastq_handler=FastqHandler(context.obj),
                case=link_obj.family.internal_id,
                sample=link_obj.sample.internal_id,
            )
        else:
            LOG.warning(f"{case_id} has no linked samples")
            click.Abort()
    else:
        LOG.warning(f"{case_id} is not present in database")
        click.Abort()


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("--panel-bed", required=False, help="Optional")
@click.pass_context
def config_case(context, panel_bed, case_id, dry):
    """Create config file for BALSAMIC analysis for a case"""

    LOG.info(f"Creating config for {case_id}")

    arguments = {
        "case_id": case_id,
        "normal": None,
        "tumor": None,
        "panel_bed": None,
        "output_config": f"{case_id}.json",
    }
    acceptable_applications = {"wgs", "wes", "tgs"}
    applications_requiring_bed = {"wes", "tgs"}

    case_object = context.obj["MetaBalsamicAPI"].lookup_samples(case_id)
    if case_object:
        if case_object.links:
            setup_data = context.obj["MetaBalsamicAPI"].get_case_config_params(
                case_id, case_object.links
            )

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

            # Check if normal samples are 1 or 0
            if len(normal_paths) == 1:
                arguments["normal"] = normal_paths[0]
            elif len(normal_paths) == 0:
                arguments["normal"] = None
            elif len(normal_paths) > 1:
                LOG.warning(f"Too many normal samples found: {len(normal_paths)}")
                click.Abort()

            # Check if tumor samples are 1
            if len(tumor_paths) == 1:
                arguments["tumor"] = tumor_paths[0]
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
                        arguments["panel_bed"] = (
                            context.obj["MetaBalsamicAPI"].balsamic_api.bed_path
                            + "/"
                            + target_beds.pop()
                        )
                else:
                    arguments["panel_bed"] = None
        else:
            LOG.warning(f"{case_id} has no linked samples")
            click.Abort()
    else:
        LOG.warning(f"{case_id} is not present in database")
        click.Abort()

    context.obj["MetaBalsamicAPI"].balsamic_api.config_case(arguments)


@balsamic.command()
@click.option("-d", "--dry-run", "dry", is_flag=True, help="print command to console")
@click.option(
    "-r", "--run-analysis", "run_analysis", is_flag=True, default=False, help="start analysis",
)
@click.option("--config", "config_path", required=False, help="Optional")
@ANALYSIS_TYPE_OPTION
@PRIORITY_OPTION
@EMAIL_OPTION
@click.argument("case_id")
@click.pass_context
def run(context, dry, run_analysis, config_path, priority, email, case_id, analysis_type):
    """Generate a config for the case_id."""

    conda_env = context.obj["balsamic"]["conda_env"]
    slurm_account = context.obj["balsamic"]["slurm"]["account"]
    priority = priority if priority else context.obj["balsamic"]["slurm"]["qos"]
    root_dir = Path(context.obj["balsamic"]["root"])
    if not config_path:
        config_path = Path.joinpath(root_dir, case_id, case_id + ".json")

    # Call Balsamic
    command_str = f" run analysis --account {slurm_account} -s {config_path}"

    if run_analysis:
        command_str += " --run-analysis"

    if email:
        command_str += f" --mail-user {email}"

    if analysis_type:
        command_str += f" --analysis-type {analysis_type}"

    command_str += f" --qos {priority}"

    command = f"bash -c 'source activate {conda_env}; balsamic run analysis --account {slurm_account} -s {config_path}{command_str}'"

    if dry:
        LOG.info(" ".join(command))
        return SUCCESS

    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):
    """Remove stored FASTQ files"""

    work_dir = Path(f"{context.obj['MetaBalsamicAPI'].balsamic_api.root_dir}/{case_id}/fastq")
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
