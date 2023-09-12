"""CLI options for Nextflow and NF-Tower."""

import click

OPTION_WORKDIR = click.option(
    "--work-dir",
    type=click.Path(),
    help="Directory where intermediate result files are stored",
)
OPTION_RESUME = click.option(
    "--resume",
    is_flag=True,
    default=False,
    show_default=True,
    help="Execute the script using the cached results, useful to continue \
        executions that was stopped by an error",
)
OPTION_PROFILE = click.option(
    "--profile",
    type=str,
    show_default=True,
    help="Choose a configuration profile",
)

OPTION_LOG = click.option(
    "--log",
    type=click.Path(),
    help="Set nextflow log file path",
)

OPTION_CONFIG = click.option(
    "--config",
    type=click.Path(),
    help="Nextflow config file path",
)

OPTION_PARAMS_FILE = click.option(
    "--params-file",
    type=click.Path(),
    help="Nextflow pipeline-specific parameter file path",
)

OPTION_USE_NEXTFLOW = click.option(
    "--use-nextflow",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Execute pipeline using nextflow",
)

OPTION_REVISION = click.option(
    "--revision",
    type=str,
    help="Revision of workflow to run (either a git branch, tag or commit SHA number)",
)
OPTION_COMPUTE_ENV = click.option(
    "--compute-env",
    type=str,
    help="Compute environment name. If not specified the primary compute environment will be used.",
)
OPTION_TOWER_RUN_ID = click.option(
    "--nf-tower-id",
    type=str,
    is_flag=False,
    default=None,
    help="NF-Tower ID of run to relaunch. If not provided the latest NF-Tower ID for a case will be used.",
)
