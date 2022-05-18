import click

from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos

OPTION_GENOME_VERSION = click.option(
    "--genome-version",
    show_default=True,
    default=GenomeVersion.hg19,
    type=click.Choice([GenomeVersion.hg19, GenomeVersion.hg38, GenomeVersion.canfam3]),
    help="Type and build version of the reference genome. Set this option to override the default.",
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
)
OPTION_ANALYSIS_TYPE = click.option(
    "-a",
    "--analysis-type",
    type=click.Choice(["qc", "paired", "single"]),
    help="Setting this option to qc ensures only QC analysis is performed",
)
OPTION_RUN_ANALYSIS = click.option(
    "-r",
    "--run-analysis",
    is_flag=True,
    default=False,
    help="Execute BALSAMIC in non-dry mode",
)
OPTION_QOS = click.option(
    "-qos",
    "--slurm-quality-of-service",
    type=click.Choice([SlurmQos.LOW, SlurmQos.NORMAL, SlurmQos.HIGH, SlurmQos.EXPRESS]),
    help="Job priority in SLURM. Setting this option will override the StatusDB case priority.",
)
OPTION_PON_CNN = click.option(
    "--pon-cnn",
    type=click.Path(exists=True),
    required=False,
    help="Panel of normal reference (.cnn) for cnvkit",
)
