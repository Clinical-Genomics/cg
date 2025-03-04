import logging
import re
from pathlib import Path

import rich_click as click

from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.io.gzip import read_gzip_first_line
from cg.io.txt import write_txt
from cg.meta.workflow.fastq import _is_undetermined_in_path
from cg.models.fastq import FastqFileMeta, GetFastqFileMeta

LOG = logging.getLogger(__name__)


def write_content_to_file_or_stdout(content: str, file_path: Path, dry_run: bool = False) -> None:
    """Write content to a file if dry-run is False, otherwise print to stdout."""
    if dry_run:
        click.echo(content)
        return
    write_txt(content=content, file_path=file_path)


def get_sex_code(sex: str) -> int:
    """Return Raredisease sex code."""
    LOG.debug("Translate sex to integer code")
    try:
        code = PlinkSex[sex.upper()]
    except KeyError:
        raise ValueError(f"{sex} is not a valid sex")
    return code


def get_phenotype_code(phenotype: str) -> int:
    """Return Raredisease phenotype code."""
    LOG.debug("Translate phenotype to integer code")
    try:
        code = PlinkPhenotypeStatus[phenotype.upper()]
    except KeyError:
        raise ValueError(f"{phenotype} is not a valid phenotype")
    return code


def extract_read_files(
    metadata: list[FastqFileMeta], forward_read: bool = False, reverse_read: bool = False
) -> list[str]:
    """Extract a list of fastq file paths for either forward or reverse reads."""
    if forward_read and not reverse_read:
        read_direction = 1
    elif reverse_read and not forward_read:
        read_direction = 2
    else:
        raise ValueError("Either forward or reverse needs to be specified")
    sorted_metadata: list = sorted(metadata, key=lambda k: k.path)
    return [
        fastq_file.path
        for fastq_file in sorted_metadata
        if fastq_file.read_direction == read_direction
    ]


def parse_fastq_data(fastq_path: Path) -> FastqFileMeta:
    header_line: str = read_gzip_first_line(file_path=fastq_path)
    fastq_file_meta: FastqFileMeta = parse_fastq_header(header_line)
    fastq_file_meta.path = fastq_path
    fastq_file_meta.undetermined = _is_undetermined_in_path(fastq_path)
    matches = re.findall(r"-l[1-9]t([1-9]{2})_", str(fastq_path))
    if len(matches) > 0:
        fastq_file_meta.flow_cell_id = f"{fastq_file_meta.flow_cell_id}-{matches[0]}"
    return fastq_file_meta


def parse_fastq_header(line: str) -> FastqFileMeta | None:
    """Parse and return fastq header metadata.
    Handle Illumina's two different header formats
    @see https://en.wikipedia.org/wiki/FASTQ_format
    Raise:
        TypeError if unable to split line into expected parts.
    """
    parts = line.split(":")
    try:
        return GetFastqFileMeta.header_format.get(len(parts))(parts=parts)
    except TypeError as exception:
        LOG.error(f"Could not parse header format for header: {line}")
        raise exception
