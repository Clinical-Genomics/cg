from pathlib import Path

import click

SAMPLE_SHEET_HEADERS = {
    "bcl2fastq": [
        "FCID",
        "Lane",
        "SampleID",
        "SampleRef",
        "index",
        "index2",
        "SampleName",
        "Control",
        "Recipe",
        "Operator",
        "Project",
    ],
    "dragen": [
        "FCID",
        "Lane",
        "Sample_ID",
        "SampleRef",
        "index",
        "index2",
        "SampleName",
        "Control",
        "Recipe",
        "Operator",
        "Sample_Project",
    ],
}

SAMPLE_SHEET_DATA_HEADER = "[Data]"

DRAGEN_BARCODE_MISMATCH = ["BarcodeMismatchIndex1,#", "BarcodeMismatchIndex2,#"]

OPTION_BCL_CONVERTER = click.option(
    "-b",
    "--bcl-converter",
    type=click.Choice(["bcl2fastq", "dragen"]),
    default="bcl2fastq",
    help="Specify bcl conversion software. Choose between bcl2fastq and dragen. Default is "
    "bcl2fastq.",
)

FASTQ_FILE_SUFFIXES = [".fastq", ".gz"]

DEMUX_STATS_PATH = {
    "bcl2fastq": {
        "demultiplexing_stats": Path("Stats") / Path("DemultiplexingStats.xml"),
        "conversion_stats": Path("Stats") / Path("ConversionStats.xml"),
        "runinfo": None,
    },
    "dragen": {
        "demultiplexing_stats": Path("Reports") / Path("Demultiplex_Stats.csv"),
        "conversion_stats": Path("Reports") / Path("Demultiplex_Stats.csv"),
        "adapter_metrics_stats": Path("Reports") / Path("Adapter_Metrics.csv"),
        "runinfo": Path("Reports") / Path("RunInfo.xml"),
    },
}

DRAGEN_PASSED_FILTER_PCT = 100.00000
