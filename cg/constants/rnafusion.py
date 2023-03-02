"""RNAfusion related constants."""

from cgmodels.cg.constants import StrEnum

from cg.constants.nextflow import NFX_SAMPLESHEET_HEADERS

RNAFUSION_ACCEPTED_STRANDEDNESS = ["forward", "reverse", "unstranded"]
RNAFUSION_STRANDEDNESS_HEADER = "strandedness"
RNAFUSION_SAMPLESHEET_HEADERS = NFX_SAMPLESHEET_HEADERS + [RNAFUSION_STRANDEDNESS_HEADER]


class RnafusionDefaults:
    """Rnafusion default parameters"""

    STRANDEDNESS: str = "reverse"
    TRIM: bool = True
    FUSIONINSPECTOR_FILTER: bool = True
    ALL: bool = True
    PIZZLY: bool = True
    SQUID: bool = True
    STARFUSION: bool = True
    FUSIONCATCHER: bool = True
    ARRIBA: bool = True
