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
