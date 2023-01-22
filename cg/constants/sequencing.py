"""Constants related to all things sequencing."""
from enum import Enum

from cgmodels.cg.constants import StrEnum


class SequencingPlatform(str, Enum):
    """Sequencing platform"""

    ILLUMINA = "illumina"


class PreparationCategory(str, Enum):
    SARS2_COV = "cov"
    MICRO = "mic"
    READY_MADE_LIBRARY = "rml"
    TARGETED_GENOME_SEQUENCING = "tgs"
    WHOLE_EXOME_SEQUENCING = "wes"
    WHOLE_GENOME_SEQUENCING = "wgs"
    WHOLE_TRANSCRIPTOME_SEQUENCING = "wts"


class SequencingMethod(StrEnum):
    """Sequencing method types."""

    TGS: str = "tgs"
    WES: str = "wes"
    WGS: str = "wgs"
    WTS: str = "wts"


class Sequencers(StrEnum):
    """Sequencer instruments."""

    HISEQX: str = "hiseqx"
    HISEQGA: str = "hiseqga"
    NOVASEQ: str = "novaseq"
    ALL: str = "all"


sequencer_types = {
    "D00134": Sequencers.HISEQGA,
    "D00410": Sequencers.HISEQGA,
    "D00415": Sequencers.HISEQGA,
    "D00450": Sequencers.HISEQGA,
    "D00456": Sequencers.HISEQGA,
    "D00483": Sequencers.HISEQGA,
    "M03284": Sequencers.HISEQGA,
    "SN1025": Sequencers.HISEQGA,
    "SN7001298": Sequencers.HISEQGA,
    "SN7001301": Sequencers.HISEQGA,
    "ST-E00198": Sequencers.HISEQX,
    "ST-E00201": Sequencers.HISEQX,
    "ST-E00214": Sequencers.HISEQX,
    "ST-E00266": Sequencers.HISEQX,
    "ST-E00269": Sequencers.HISEQX,
    "A00187": Sequencers.NOVASEQ,
    "A00621": Sequencers.NOVASEQ,
    "A00689": Sequencers.NOVASEQ,
}


class Variants(StrEnum):
    """Type of variants."""

    SNV: str = "snv"
    SV: str = "sv"
