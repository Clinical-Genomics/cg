import csv

from cg.store.models import (
    SequencingStatistics,
)


def parse_bcl2fastq_metrics(demultiplexing_directory: str) -> SequencingStatistics:
    """
    Parse the sequencing metrics for a flow cell demultiplexed using bcl2fastq.
    Args:
        demultiplexing_directory: Path to a directory with data from a flow cell demultiplexed with bcl2fastq
    """
    pass


def get_sample_sheet(demux_dir):
    sample_sheet = []
    samplesheet_file_name = f"{demux_dir}/SampleSheet.csv"

    with open(samplesheet_file_name, "r") as samplesheet_fh:
        reader = csv.reader(samplesheet_fh)
        header = []
        for line in reader:
            if line[0].startswith("["):
                continue
            if line[2] == "SampleID":
                header = line
                continue

            entry = dict(zip(header, line))
            sample_sheet.append(entry)

    return sample_sheet
