"""Constants related to sequencing."""
from cg.utils.enums import StrEnum


class Sequencers(StrEnum):
    """Sequencer instruments."""

    ALL: str = "all"
    HISEQX: str = "hiseqx"
    HISEQGA: str = "hiseqga"
    NOVASEQ: str = "novaseq"
    NOVASEQX: str = "novaseqx"
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
    "LH00188": Sequencers.NOVASEQX,
    "LH00202": Sequencers.NOVASEQX,
    "LH00217": Sequencers.NOVASEQX,
}

FLOWCELL_Q30_THRESHOLD = {
    Sequencers.HISEQX: 75,
    Sequencers.HISEQGA: 80,
    Sequencers.NOVASEQ: 75,
    Sequencers.NOVASEQX: 75,
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


class RecordType(StrEnum):
    Sample: str = "Sample"
    Pool: str = "Pool"


class SequencingPlatform(StrEnum):
    ILLUMINA: str = "ILLUMINA"
    OXFORD_NANOPORE: str = "OXFORD_NANOPORE"
