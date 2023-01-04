"""RNAfusion related constants."""


from cg.constants import ReportTypes
from cg.constants.nextflow import NFX_SAMPLESHEET_HEADERS

RNAFUSION_STRANDEDNESS_DEFAULT = "reverse"
RNAFUSION_ACCEPTED_STRANDEDNESS = ["forward", "reverse", "unstranded"]
RNAFUSION_STRANDEDNESS_HEADER = "strandedness"
RNAFUSION_SAMPLESHEET_HEADERS = NFX_SAMPLESHEET_HEADERS + [RNAFUSION_STRANDEDNESS_HEADER]
RNAFUSION_REPORTS = [
    str(ReportTypes.MULTIQC_RNA_REPORT),
    str(ReportTypes.GENE_FUSION_REPORT),
    str(ReportTypes.RNAFUSION_REPORT),
    str(ReportTypes.RNAFUSION_INSPECTOR_REPORT),
]
