import click

from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos
from cg.constants.subject import Sex

OPTION_GENDER = click.option(
    "--gender",
    type=click.Choice([Sex.FEMALE, Sex.MALE]),
    required=False,
    help="Case associated gender. Set this option to override the one selected by the customer in StatusDB.",
)
OPTION_GENOME_VERSION = click.option(
    "--genome-version",
    show_default=True,
    default=GenomeVersion.HG19,
    type=click.Choice([GenomeVersion.HG19, GenomeVersion.HG38, GenomeVersion.CANFAM3]),
    help="Type and build version of the reference genome. Set this option to override the default.",
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
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
    help="Panel of normal reference (.cnn) for CNVkit",
)
OPTION_OBSERVATIONS = click.option(
    "--observations",
    type=click.Path(exists=True),
    multiple=True,
    required=False,
    help="VCF paths of clinical and/or cancer SNVs and SVs observations (WGS analysis only). Set this option to "
    "override the latest Loqusdb dump files.",
)

OPTION_CACHE_VERSION = click.option(
    "--cache-version",
    type=click.STRING,
    required=False,
    help="Cache version to be used for init or analysis. Use 'develop' or 'X.X.X'.",
)

OPTION_CLUSTER_CONFIG = click.option(
    "--cluster-config",
    type=click.Path(exists=True),
    required=False,
    help="Cluster resources configuration JSON file path used for analysis.",
)
