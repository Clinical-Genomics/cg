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
from cg.cli.workflow.balsamic.store import store as store_cmd
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd
from cg.cli.workflow.get_links import get_links
from cg.exc import LimsDataError, BalsamicStartError
from cg.meta.workflow.base import get_target_bed_from_lims
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store
from cg.utils.commands import Process
from pathlib import Path
from cg.utils.fastq import FastqAPI
from cg.meta.deliver import DeliverAPI

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option("-d",
                          "--dry-run",
                          "dry",
                          help="Print command to console without executing")


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

        command = ("config", "case")

        opts = {
            "--analysis-dir": self.root_dir,
            "--singularity": self.singularity,
            "--reference-config": self.reference_config,
            "--case-id": arguments["case_id"],
            "--normal": arguments["normal"],
            "--output-config": arguments["output_config"],
            "--panel-bed": arguments["panel_bed"],
            "--tumor": arguments["tumor"],
        }

        opts = sum([(k, v) for k, v in opts if v], ())
        self.process.run_command(command + opts)

    def run_analysis(self, arguments: dict):
        """Execute BALSAMIC"""

        command = ("run", "analysis")

        opts = {
            "--account": self.slurm,
            "--mail-user": self.email,
            "--qos": self.qos,
            "--sample-config": arguments["sample_config"],
            "--analysis-type": arguments["analysis_type"],
            "--run-analysis": arguments["run_analysis"],
        }

        opts = sum([(k, v) for k, v in opts if v], ())
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
        self.fastq_api = FastqAPI

    def get_deliverables_file_path(self, case_id):
        """Generates a path where the Balsamic deliverables file for the case_id should be
        located"""
        return Path(self.balsamic_api.root_dir / case_id / "delivery_report" /
                    (case_id + ".hk"))

    def get_config_path(self, case_id):
        """Generates a path where the Balsamic config for the case_id should be located"""
        return Path(self.balsamic_api.root_dir / case_id / (case_id + ".json"))

    def get_file_collection(self, sample):
        file_objs = self.housekeeper_api.files(bundle=sample, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_api.parse_header(header_line)

            data = {
                "path": file_obj.full_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("_Undetermined_" in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        return files

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

            if link_object.sample.data_analysis and "balsamic" in link_object.sample.data_analysis.lower(
            ):
                LOG.info("%s has balsamic as data analysis, linking.",
                         link_object.sample.internal_id)

                file_collection = self.get_file_collection(
                    sample=link_object.sample.internal_id)
                self.fastq_handler.link(case=link_object.family.internal_id,
                                        sample=link_object.sample.internal_id,
                                        files=file_collection)

            else:
                LOG.info(
                    "%s does not have blasamic as data analysis, skipping.",
                    link_object.sample.internal_id)

        LOG.info("Linking completed")

    def get_case_config_params(self, case_id, case_object_links) -> dict:
        """Determines correct config params and returns them in a dict"""

        setup_data = {}
        #Iterate over all links
        for link_object in case_object_links:
            #Check of Balsamic as analysis type
            if link_object.sample.data_analysis and "balsamic" in link_object.sample.data_analysis.lower(
            ):

                #Get file collection for sample id
                file_collection = self.get_file_collection(
                    sample=link_object.sample.internal_id)
                fastq_data = file_collection[0]
                linked_fastq_name = self.fastq_handler.FastqFileNameCreator.create(
                    lane=fastq_data["lane"],
                    flowcell=fastq_data["flowcell"],
                    sample=link_object.sample.internal_id,
                    read=fastq_data["read"],
                    more={"undetermined": fastq_data["undetermined"]})
                concatenated_fastq_name = self.fastq_handler.FastqFileNameCreator.get_concatenated_name(
                    linked_fastq_name)
                concatenated_path = f"{self.balsamic_api.root_dir}/{case_id}/{concatenated_fastq_name}"

                #Block to get application type
                application_type = link_object.sample.application_version.application.prep_category

                #Block to get panel BED
                target_bed_filename = get_target_bed_from_lims(
                    lims=self.lims_api,
                    status_db=self.store,
                    target_bed=link_object.sample.internal_id)

                #Check if tumor
                if link_object.sample.is_tumour:
                    tissue_type = "tumor"
                else:
                    tissue_type = "normal"
                setup_data[link_object.sample.internal_id] = {
                    "tissue_type": tissue_type,
                    "concatenated_path": concatenated_path,
                    "application_type": application_type,
                    "target_bed": target_bed_filename,
                }

        return setup_data

    def get_run_params(self) -> dict:
        """Determines correct config params and returns them in a dict"""
        pass


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
            arguments = {
                "case_id": case_id,
                "normal": "",
                "tumor": "",
                "panel_bed": "",
                "output_config": f"{case_id}.json"
            }

            acceptable_applications = {"wgs", "wes", "tgs"}
            applications_requiring_bed = {"wes", "tgs"}
            setup_data = context.obj["MetaBalsamicAPI"].get_case_config_params(
                case_id, case_object.links)

            #Can be handled with pandas eloquently in future
            normal_paths = [
                v["concatenated_path"] for k, v in setup_data
                if v["tissue_type"] == "normal"
            ]
            tumor_paths = [
                v["concatenated_path"] for k, v in setup_data
                if v["tissue_type"] == "tumor"
            ]
            application_types = set(
                [v["application_type"] for k, v in setup_data])
            target_beds = set([v["target_bed"] for k, v in setup_data])

            #Check if normal samples are 1
            if len(normal_paths) == 1:
                arguments["normal"] = normal_paths[0]
            elif len(normal_paths) == 0:
                arguments["normal"] = None
            elif len(normal_paths) > 1:
                LOG.warning(
                    f"Too many normal samples found: {len(normal_paths)}")
                click.Abort()

            #Check if tumor samples are 1
            if len(tumor_paths) == 1:
                arguments["tumor"] = normal_paths[0]
            elif len(tumor_paths) == 0:
                LOG.warning(f"No tumor samples found for {case_id}")
                click.Abort()
            elif len(tumor_paths) > 1:
                LOG.warning(
                    f"Too many tumor samples found: {len(tumor_paths)}")
                click.Abort()

            #Check application type is only one
            if len(application_types) > 1:
                LOG.warning(
                    f"More than one application found for case {case_id}")
                click.Abort()
            elif len(application_types) == 0:
                LOG.warning(f"No application found for case {case_id}")
                click.Abort()

            #Check if application type is suitable for BALSAMIC
            if application_types.issubset(acceptable_applications):
                LOG.info(f"Application type {application_types}")
            else:
                LOG.warning(f"Improper application type for case {case_id}")
                click.Abort()

            #If panel BED is provided, check if panel BED is compatible with application type
            if panel_bed:
                if application_types.issubset(applications_requiring_bed):
                    arguments["panel_bed"] = panel_bed
                else:
                    LOG.warning(
                        f"Panel BED {panel_bed} incompatible with application type"
                    )
                    click.Abort()
            #If panel BED is not provided, it should be inferred.
            else:
                if application_types.issubset(applications_requiring_bed):
                    if len(target_beds) == 0:
                        LOG.warning(
                            f"Panel BED cannot be found for sample {case_id}")
                        click.Abort()
                    elif len(target_beds) > 1:
                        LOG.warning(
                            f"Multiple Panel BED indicated for sample {case_id}"
                        )
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


@balsamic.command
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
@click.option("-a",
              "--analysis-type",
              type=click.Choice(["qc", "paired", "single"]))
@click.option("-r",
              "--run-analysis",
              is_flag=True,
              default=False,
              help="Execute in non-dry mode")
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):

    arguments = {
        "priority": None,
        "analysis_type": None,
        "run_analysis": False
    }
    if priority:
        arguments["priority"] = priority
    if analysis_type:
        arguments["analysis_type"] = analysis_type
    if run_analysis:
        arguments["run_analysis"] = run_analysis

    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)


@balsamic.command
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


@balsamic.command
@ARGUMENT_CASE_ID
@click.pass_context
def start(context, case_id):
    """Invoke all commands"""

    context.invoke(link)
    context.invoke(config_case)
    context.invoke(run)
    context.invoke(remove_fastq)
