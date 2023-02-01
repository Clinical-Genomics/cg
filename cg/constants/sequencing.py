"""Constants related to all things sequencing"""
from cgmodels.cg.constants import StrEnum


class Sequencers(StrEnum):
    """Sequencer instruments."""

    ALL: str = "all"
    HISEQX: str = "hiseqx"
    HISEQGA: str = "hiseqga"
    NOVASEQ: str = "novaseq"
    OTHER: str = "other"


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
    "A01901": Sequencers.NOVASEQ,
}


class SequencingMethod(StrEnum):
    """Sequencing method types."""

    TGS: str = "tgs"
    WES: str = "wes"
    WGS: str = "wgs"
    WTS: str = "wts"


class Variants(StrEnum):
    """Type of variants."""

    SNV: str = "snv"
    SV: str = "sv"
