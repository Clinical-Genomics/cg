import gzip
import logging
import re
import subprocess
import sys
import shutil
import click

from pathlib import Path
from cg.apps import hk, scoutapi, lims, tb
from cg.apps.balsamic.fastq import FastqHandler
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd, CASE_TAGS, SAMPLE_TAGS
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.base import get_panel_bed_from_lims
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store
from cg.utils.commands import Process
from cg.utils import Process
from cg.store import Store
from cg.apps.hk import HousekeeperAPI



LOG = logging.getLogger(__name__)   

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option("-d", "--dry-run", "dry", help="Print command to console without executing")


class BalsamicAPI:

    """Handles execution of BALSAMIC"""

    def __init__(self, config):
        self.binary = config["balsamic"]["executable"]
        self.singularity = config["balsamic"]["singularity"]
        self.reference_config = config["balsamic"]["reference_config"]
        self.email = config["balsamic"]["email"]
        self.root_dir = config["balsamic"]["root"]
        self.slurm = config["balsamic"]["slurm"]["account"]
        self.qos = config["balsamic"]["slurm"]["qos"]
        self.process = Process(self.binary)


    def config_case(self, arguments: dict):
        """Create config file for BALSAMIC analysis"""

        command = ["config", "case"]

        opts = [
            "--analysis-dir", self.root_dir,
            "--singularity", self.singularity,
            "--reference-config", self.reference_config,

            "--case-id", arguments["case_id"],
            "--normal", arguments["normal"],
            "--output-config", arguments["output_config"],
            "--panel-bed", arguments["panel_bed"],
            "--tumor", arguments["tumor"],
            ]

        self.process.run_command(command)


    def run_analysis(self, arguments: dict):
        """Execute BALSAMIC"""

        command = [
            "run", 
            "analysis",
            "--account", arguments["account"],
            "--analysis-type", arguments["analysis_type"],
            "--mail-user", arguments["mail_user"],
            "--run-analysis", arguments["run_analysis"],
            "--sample-config", arguments["sample_config"],
            "--qos", arguments["qos"],
            ]


        self.process.run_command(command)





class MetaBalsamicAPI:
    """Handles communication between BALASMIC processes 
    and the rest of CG infrastructure"""

    def __init__(self, config):

        self.balsamic_api = BalsamicAPI(config)
        self.store = Store(config["database"])
        self.housekeeper_api = hk.HousekeeperAPI(config)
        self.fastq_handler = FastqHandler(config)
        self.lims_api = lims.LimsAPI(config)
        self.scout_api = scoutapi.ScoutAPI(config)
        self.trailblazer_api = tb.TrailblazerAPI(config)
        self.deliver_api = DeliverAPI(
                                    hk_api=self.housekeeper_api, 
                                    lims_api=self.lims_api, 
                                    case_tags = CASE_TAGS, 
                                    sample_tags = SAMPLE_TAGS,
                                    )

        self.analysis_api = AnalysisAPI(
                                    db = self.store,
                                    hk_api = self.housekeeper_api,
                                    tb_api = self.trailblazer_api,
                                    scout_api = self.scout_api,
                                    lims_api = self.lims_api,
                                    deliver_api = self.deliver_api,
                                    )

    def lookup_samples(self, case_id):
        """Look up case ID in StoreDB and return result"""

        case_object = self.store.family(case_id)
        return case_object


    def link_samples(self, case_object_links):

        for link_object in case_object_links:
            LOG.info(
                "%s: %s link FASTQ files",
                link_object.sample.internal_id,
                link_object.sample.data_analysis,
                )

            if link_object.sample.data_analysis and "balsamic" in link_object.sample.data_analysis.lower():
                LOG.info(
                    "%s has balsamic as data analysis, linking.",
                    link_object.sample.internal_id
                    )

                self.analysis_api.link_sample(
                                            fastq_handler=self.fastq_handler,
                                            case=link_object.family.internal_id,
                                            sample=link_object.sample.internal_id
                                            )
            else:
                LOG.warning(
                    "%s does not have blasamic as data analysis, skipping.",
                    link_object.sample.internal_id
                    )

        LOG.info("Linking completed")




    def get_case_config_params(self, panel_bed, case_id) -> dict:
        """Determines correct config params and returns them in a dict"""




        arguments = {

            #argument
            "--case-id": case_id,
            "--output_config": f'{case_id}.json',

            #command line or API logic
            "panel_bed": panel_bed ,

            #API-only logic
            "--normal", arguments["normal"],
            "--tumor", arguments["tumor"],
        }
        return arguments


    def get_panel_bed_param(self, case_object_links) -> dict:
        pass

    def get_tumor_param(self, case_object_links) -> dict:
        pass

    def get_normal_param(self, case_object_links) -> dict:
        pass


    def get_run_params(self) -> dict:
        """Determines correct config params and returns them in a dict"""
        pass



#Calling
@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context):
    """Initialize MetaBalsamicAPI"""
    context.obj["MetaBalsamicAPI"] = MetaBalsamicAPI(context.obj)



@balsamic.command
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




@balsamic.command
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
            #can run config






            
        else:
            LOG.warning(f"{case_id} has no linked samples")
            click.Abort()
    else:
        LOG.warning(f"{case_id} is not present in database")
        click.Abort()


    arguments = context.obj["MetaBalsamicAPI"].get_case_config_params(panel_bed, case_id)



@balsamic.command
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("-p","--priority", type=click.Choice(["low", "normal", "high"]))
@click.option("-a","--analysis-type", type=click.Choice["qc", "paired", "single"])
@click.option("-r","--run-analysis", is_flag=True, default=False, help="Execute in non-dry mode")
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):
    arguments = context.obj["MetaBalsamicAPI"].get_run_params()
    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)


@balsamic.command
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):    
    """Remove stored FASTQ files"""

    work_dir = Path(f'{context.obj['balsamic']['root']}/{case_id}/fastq')
    if work_dir.exists():
        shutil.rmtree(work_dir)
        LOG.info(f"Path {work_dir} removed successfully")
    else:
        LOG.info(f"Path {work_dir} does not exist")



@balsamic.command
@ARGUMENT_CASE_ID
@click.pass_context
def start(context, case_id):
    """Invoke all commands"""

    context.invoke(link)
    context.invoke(config_case)
    context.invoke(run)
    context.invoke(remove_fastq)



