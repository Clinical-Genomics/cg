from cg.utils import Process
from cg.store import Store
from cg.apps.hk import HousekeeperAPI



LOG = logging.getLogger(__name__)


        
ARGUMENT_CASE_ID = click.argument("case_id")


OPTION_DRY = click.option("-d", "--dry-run", "dry", help="Print command to console without executing")
OPTION_PRIORITY = click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))



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


    def config_case(self, dry, arguments: dict):
        """Create config file for BALSAMIC analysis"""

        command = [
            "config", 
            "case",
            "--adapter-trim", arguments["adapter_trim"], 
            "--analysis-dir", arguments["analysis_dir"],
            "--case-id", arguments["case_id"],
            "--umi", arguments["umi"],
            "--umi-trim-length", arguments["umi_trim_length"],
            "--normal", arguments["normal"],
            "--output-config", arguments["output_config"],
            "--panel-bed", arguments["panel_bed"],
            "--quality-trim", arguments["quality_trim"],
            "--reference-config", arguments["reference_config"],
            "--singularity", arguments["singularity"],
            "--tumor", arguments["tumor"],
            ]

        if dry:
            click.echo(command)
        else:
            self.process.run_command(command)


    def run_analysis(self, dry, arguments: dict):
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

        if dry:
            click.echo(command)
        else:
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
        





    def link_samples(self, case_id):
        """Links Sample ID and Case ID """
        pass

    def get_case_config_params(self, case_id) -> dict:
        """Determines correct config params and returns them in a dict"""


        arguments = {
            
            #hardcoded
            "analysis_dir": self.root_dir,
            "case_id": case_id,
            "singularity": self.singularity,
            "reference_config": self.reference_config,
            "output_config": f'{case_id}.json',


            #command line or API logic
            "--panel-bed", arguments["panel_bed"],

            #API-only logic
            "--normal", arguments["normal"],
            "--tumor", arguments["tumor"],
        }
        return arguments


    def get_run_params(self):
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
    #only case id
    if input_type == "case_id":
        #Link by case id
        continue
    elif input_type == "sample_id":
        #Link by sample id
        continue


    pass


@balsamic.command
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("--target-bed", required=False, help="Optional")
@click.pass_context
def config_case(context, adapter_trim, quality_trim, target_bed, umi, umi_trim_length, case_id):
    arguments = context.obj["MetaBalsamicAPI"].get_run_params()
    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)
    pass


@balsamic.command
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@click.option("-a","--analysis-type", type=click.Choice["qc", "paired", "single"])
@click.option("-r","--run-analysis", is_flag=True, default=False, help="start analysis")
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id):

    arguments = context.obj["MetaBalsamicAPI"].get_case_config_params()
    context.obj["MetaBalsamicAPI"].balsamic_api.run_analysis(arguments)

    pass


@balsamic.command
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):
    """Remove stored FASTQ files"""

    work_dir = Path(f'{context.obj['balsamic']['root']}/{case_id}/fastq')

    if work_dir.exists():
        shutil.rmtree(work_dir)
        LOG.info("Removed successfully")
    else:
        LOG.info("Does not exist")



@balsamic.command
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context, dry, case_id):
    context.invoke(link)

    """Invoke link, config_case and run commands"""
    pass




