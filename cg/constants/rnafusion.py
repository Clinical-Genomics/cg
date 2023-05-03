"""RNAfusion related constants."""


from cg.constants.nextflow import NFX_SAMPLESHEET_HEADERS

RNAFUSION_ACCEPTED_STRANDEDNESS = ["forward", "reverse", "unstranded"]
RNAFUSION_STRANDEDNESS_HEADER = "strandedness"
RNAFUSION_SAMPLESHEET_HEADERS = NFX_SAMPLESHEET_HEADERS + [RNAFUSION_STRANDEDNESS_HEADER]
RNAFUSION_METRIC_CONDITIONS: dict = {
    "uniquely_mapped_percent": {"norm": "gt", "threshold": 60},
    "PCT_MRNA_BASES": {"norm": "gt", "threshold": 80},
    "PCT_RIBOSOMAL_BASES": {"norm": "lt", "threshold": 5},
    "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.7},
}


class RnafusionDefaults:
    """Rnafusion default parameters"""

    STRANDEDNESS: str = "reverse"
    TRIM: bool = False
    FASTP_TRIM: bool = True
    TRIM_TAIL: int = 50
    FUSIONREPORT_FILTER: bool = False
    FUSIONINSPECTOR_FILTER: bool = False
    ALL: bool = False
    PIZZLY: bool = False
    SQUID: bool = False
    STARFUSION: bool = True
    FUSIONCATCHER: bool = True
    ARRIBA: bool = True
    CRAM: str = "arriba,starfusion"
