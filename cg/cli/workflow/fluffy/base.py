import logging
import click
from pathlib import Path
from cg.utils import Process
from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.apps.environ import environ_email

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context):
    """Fluffy workflow"""
    if context.invoked_subcommand is None:
        LOG.info(context.get_help())
        return None
    config = context.obj
    context.obj["fluffy_analysis_api"] = FluffyAnalysisAPI(
        housekeeper_api=HousekeeperAPI(config),
        trailblazer_api=TrailblazerAPI(config),
        status_db=Store(config["database"]),
        binary=config["Fluffy"]["binary_path"],
        root_dir=config["Fluffy"]["root_dir"],
    )


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def link(context, case_id, dry_run):
    """
    Link fastq and samplesheet files from Housekeeper to analysis folder

    """
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.link_samplesheet(case_id=case_id, dry_run=dry_run)
    fluffy_analysis_api.link_fastq(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context, case_id, dry_run):
    """Run fluffy command
    Update status in CG
    Submit to Trailblazer"""
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.run_fluffy(case_id=case_id, dry_run=dry_run)
    if not dry_run:
        fluffy_analysis_api.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            email=environ_email(),
            type="tgs",
            out_dir=fluffy_analysis_api.get_output_path(case_id).as_posix(),
            config_path=fluffy_analysis_api.get_slurm_job_ids_path(case_id).as_posix(),
            priority=fluffy_analysis_api.get_priority(case_id),
            data_analysis="FLUFFY",
        )


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context, case_id, dry_run):
    """Run link and run commands"""
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, dry_run=dry_run)


@fluffy.command()
@OPTION_DRY
@click.pass_context
def start_available(context, dry_run):
    """Run link and start commands for all cases/batches ready to be analyzed
    Needs:

    """
    exit_code = EXIT_SUCCESS
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    cases_to_analyze = fluffy_analysis_api.status_db.cases_to_analyze(pipeline="fluffy")
    for case_id in cases_to_analyze:
        try:
            context.invoke(start, case_id=case_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Exception occurred - {exception_object.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()


class NIPToolAPI:
    """Class handling upload of analyses to NIPTool
    Needs:
        HK api
        NIPT upload service account
        request constructor

        send result file with post
        send multiqc file with post
        send samplesheet with post
        ???
        Profit

    """

    def __init__(self, housekeeper_api: HousekeeperAPI):
        self.housekeeper_api = housekeeper_api


class FluffyAnalysisAPI:
    def __init__(
        self,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: TrailblazerAPI,
        status_db: Store,
        root_dir: str,
        binary: str,
    ):
        self.housekeeper_api = housekeeper_api
        self.trailblazer_api = trailblazer_api
        self.status_db = status_db
        self.root_dir = Path(root_dir)
        self.process = Process(binary=binary)

    def get_samplesheet_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "samplesheet.csv")

    def get_fastq_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "fastq")

    def get_output_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output")

    def get_deliverables_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output", "deliverables.yaml")

    def get_slurm_job_ids_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "sacct.yaml")

    def get_priority(self, case_id: str) -> str:
        case_object = self.status_db.family(case_id)
        if case_object.high_priority:
            return "high"
        if case_object.low_priority:
            return "low"
        return "normal"

    def link_fastq(self, case_id: str, dry_run: bool) -> None:
        """
        1. Get fastq from HK
            1a. If split by 4 lanes, concatenate
        2. Copy sample fastq to root_dir/case_id/fastq/sample_id (from samplesheet)
        """
        case_obj = self.status_db.family(case_id)
        for familysample in case_obj.links:
            sample_id = familysample.sample.internal_id
            nipt_id = familysample.sample.name
            files = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
            for file in files:
                # Link files
                sample_path = self.get_fastq_path(case_id=case_id) / nipt_id
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    # Link and concatenate if necessary
                LOG.info(f"Linking {file.path} to {sample_path / Path(file.path).name}")

    def link_samplesheet(self, case_id: str, dry_run: bool) -> None:

        """
        1. Get samplesheet from HK
        2. Copy file to root_dir/case_id/samplesheet.csv
        """
        case_obj = self.status_db.family(case_id)
        case_name = case_obj.name
        samplesheet_housekeeper_path = Path(
            self.housekeeper_api.files(bundle=case_name, tags=["samplesheet"])[0].path
        )
        if not dry_run:
            LOG.info(f"Placeholder to actually link")

        LOG.info(
            f"Linking {samplesheet_housekeeper_path} to {self.get_samplesheet_path(case_id=case_id)}"
        )

    def run_fluffy(self, case_id: str, dry_run: bool) -> None:
        command_args = [
            "--sample",
            self.get_samplesheet_path(case_id=case_id).as_posix(),
            "--project",
            self.get_fastq_path(case_id=case_id).as_posix(),
            "--out",
            self.get_output_path(case_id=case_id).as_posix(),
            "analyse",
        ]
        self.process.run_command(command_args, dry_run=dry_run)
