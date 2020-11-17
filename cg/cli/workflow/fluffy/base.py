import logging
import click
from pathlib import Path
from cg.utils import Process

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context):
    """Base Fluffy context"""
    pass


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def link(context, case_id, dry_run):
    """
    Link fastq and samplesheet files from Housekeeper to analysis folder

    """
    pass


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context, case_id, dry_run):
    """Run fluffy command
    Update status in CG
    Submit to Trailblazer"""

    pass


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context, case_id, dry_run):
    """Run link and run commands"""
    pass


@fluffy.command()
@OPTION_DRY
@click.pass_context
def start_available(context, dry_run):
    """Run link and start commands for all cases/batches ready to be analyzed"""
    pass


class NIPToolAPI:
    """Class handling upload of analyses to NIPTool"""

    pass


class FluffyAnalysisAPI:
    def __init__(self, housekeeper_api, trailblazer_api, status_db, root_dir, binary):
        self.housekeeper_api = housekeeper_api
        self.trailblazer_api = trailblazer_api
        self.status_db = status_db
        self.root_dir = Path(root_dir)
        self.process = Process(binary=binary)

    def get_samplesheet_path(self, case_id):
        return Path(self.root_dir, case_id, "samplesheet.csv")

    def get_fastq_path(self, case_id):
        return Path(self.root_dir, case_id, "fastq")

    def get_output_path(self, case_id):
        return Path(self.root_dir, case_id, "output")

    def link_fastq(self, case_id, dry_run):
        """
        1. Get fastq from HK
            1a. If split by 4 lanes, concatenate
        2. Copy sample fastq to root_dir/case_id/fastq/sample_id (from samplesheet)
        """
        pass

    def link_samplesheet(self, case_id, dry_run):
        """
        1. Get samplesheet from HK
        2. Copy file to root_dir/case_id/samplesheet.csv
        """
        pass

    def run_fluffy(self, case_id, dry_run):
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
