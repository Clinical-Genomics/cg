"""Taxprofiler related constants."""


from cg.constants.nextflow import NFX_SAMPLE_HEADER, NFX_SAMPLESHEET_READS_HEADERS
from cg.constants.sequencing import SequencingPlatform

TAXPROFILER_RUN_ACCESSION: str = "run_accession"
TAXPROFILER_INSTRUMENT_PLATFORM: str = "instrument_platform"
TAXPROFILER_FASTA_HEADER: str = "fasta"
TAXPROFILER_SAMPLE_SHEET_HEADERS: list[str] = [
    NFX_SAMPLE_HEADER,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_INSTRUMENT_PLATFORM,
    NFX_SAMPLESHEET_READS_HEADERS,
    TAXPROFILER_FASTA_HEADER,
]
