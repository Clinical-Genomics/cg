"""Taxprofiler related constants."""


from cg.constants.nextflow import NFX_SAMPLE_HEADER, NFX_SAMPLESHEET_READS_HEADERS

TAXPROFILER_RUN_ACCESSION = "run_accession"
TAXPROFILER_INSTRUMENT_PLATFORM = "instrument_platform"
TAXPROFILER_ACCEPTED_PLATFORMS = ["ILLUMINA", "OXFORD_NANOPORE"]
TAXPROFILER_FASTA_HEADER = "fasta"
TAXPROFILER_SAMPLE_SHEET_HEADERS = [
    NFX_SAMPLE_HEADER,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_INSTRUMENT_PLATFORM,
]
TAXPROFILER_SAMPLE_SHEET_HEADERS.extend(NFX_SAMPLESHEET_READS_HEADERS)
TAXPROFILER_SAMPLE_SHEET_HEADERS.append(TAXPROFILER_FASTA_HEADER)


class TaxprofilerDefaults:
    """Taxprofiler default parameters"""

    INSTRUMENT_PLATFORM: str = "ILLUMINA"
