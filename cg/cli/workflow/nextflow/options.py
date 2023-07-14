"""CLI support for nextflow pipelines."""

import click

OPTION_LOG = click.option(
    "--log",
    type=click.Path(),
    help="Set nextflow log file path",
)
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
OPTION_TOWER = click.option(
    "--with-tower",
    is_flag=True,
    default=False,
    show_default=True,
    help="Monitor workflow execution with Seqera Tower service",
)
OPTION_STUB = click.option(
    "--stub",
    is_flag=True,
    default=False,
    show_default=True,
    help="Execute the workflow replacing process scripts with command stubs",
)
OPTION_INPUT = click.option(
    "--input", type=click.Path(exists=True), help="Path to samplesheet containing fastq files"
)
OPTION_OUTDIR = click.option(
    "--outdir", type=click.Path(), help="Path to output folder containing analysis files"
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
