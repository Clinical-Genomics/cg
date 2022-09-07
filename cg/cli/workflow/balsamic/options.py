import click

from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos
from cg.constants.subject import Gender

OPTION_GENDER = click.option(
    "--gender",
    type=click.Choice([Gender.FEMALE, Gender.MALE]),
    required=False,
    help="Case associated gender. Set this option to override the one selected by the customer in StatusDB.",
)
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
    help="Panel of normal reference (.cnn) for CNVkit",
)
OPTION_CLINICAL_SNV_OBSERVATIONS = click.option(
    "--clinical-snv-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of clinical SNV observations (WGS analysis workflow). Set this option to override the latest "
    "loqusdb dump.",
)
OPTION_CLINICAL_SV_OBSERVATIONS = click.option(
    "--clinical-sv-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of clinical SV observations (WGS analysis workflow)",
)
OPTION_CANCER_SNV_NORMAL_OBSERVATIONS = click.option(
    "--cancer-snv-normal-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of cancer SNV normal observations (WGS analysis workflow)",
)
OPTION_CANCER_SNV_TUMOR_OBSERVATIONS = click.option(
    "--cancer-snv-tumor-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of cancer SNV tumor observations (WGS analysis workflow)",
)
OPTION_CANCER_SV_NORMAL_OBSERVATIONS = click.option(
    "--cancer-sv-normal-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of cancer SV normal observations (WGS analysis workflow)",
)
OPTION_CANCER_SV_TUMOR_OBSERVATIONS = click.option(
    "--cancer-sv-tumor-observations",
    type=click.Path(exists=True),
    required=False,
    help="VCF path of cancer SV tumor observations (WGS analysis workflow)",
)
