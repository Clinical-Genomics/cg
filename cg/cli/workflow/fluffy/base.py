import logging
import click

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
def link(context, case_id, dry):
    """Link fastq files from Housekeeper to analysis folder"""
    pass


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context, case_id, dry):
    """Run fluffy command
    Update status in CG
    Submit to Trailblazer"""
    pass


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context, case_id, dry):
    """Run link and run commands"""
    pass


@fluffy.command()
@OPTION_DRY
@click.pass_context
def start_available(context, dry):
    """Run link and start commands for all cases/batches ready to be analyzed"""
    pass
