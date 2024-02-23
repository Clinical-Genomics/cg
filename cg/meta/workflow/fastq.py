"""
This module handles concatenation of balsamic fastq files.

Classes:
    FastqFileNameCreator: Creates valid balsamic filenames
    FastqHandler: Handles fastq file linking
"""

import datetime as dt
import gzip
import logging
import os
import re
import shutil
from pathlib import Path

from cg.constants import FileExtensions
from cg.io.gzip import read_gzip_first_line
from cg.models.fastq import FastqFileMeta, GetFastqFileMeta

LOG = logging.getLogger(__name__)

DEFAULT_DATE_STR = (
    "171015"  # Stand in value to use if sequencing date cannot be extracted from header
)
DEFAULT_INDEX = (
    "XXXXXX"  # Stand in value to use if flowcell index is to be masked when renaming file
)


def _is_undetermined_in_path(file_path: Path) -> bool:
    return "Undetermined" in file_path


class FastqHandler:
    """Handles fastq file linking"""

    @staticmethod
    def concatenate(files: list, concat_file: str):
        """Concatenates a list of fastq files"""
        LOG.info(FastqHandler.display_files(files, concat_file))

        with open(concat_file, "wb") as write_file_obj:
            for filename in files:
                with open(filename, "rb") as file_descriptor:
                    shutil.copyfileobj(file_descriptor, write_file_obj)

        size_before = FastqHandler.size_before(files)
        size_after = FastqHandler.size_after(concat_file)

        try:
            FastqHandler.assert_file_sizes(size_before, size_after)
        except AssertionError as error:
            LOG.warning(error)

    @staticmethod
    def size_before(files) -> int:
        """Returns the total size of the linked fastq files before concatenation"""

        return sum(os.stat(f).st_size for f in files)

    @staticmethod
    def size_after(concat_file: str) -> int:
        """returns the size of the concatenated fastq files"""

        return os.stat(concat_file).st_size

    @staticmethod
    def assert_file_sizes(size_before: int, size_after: int) -> None:
        """asserts the file sizes before and after concatenation. If the file sizes differ by more
        than 1 percent, throw an exception"""
        msg = (
            f"Warning: Large file size difference after concatenation!"
            f"Before: {size_before} -> after: {size_after}"
        )

        assert abs(size_before - size_after) / size_before <= 0.01, msg
        LOG.info("Concatenation file size check successful!")

    @staticmethod
    def display_files(files: list, concat_file: str) -> str:
        """display file names for logging purposes"""
        return (
            f"Concatenating: {', '.join(Path(file_).name for file_ in files)} -> "
            f"{Path(concat_file).name}"
        )

    @staticmethod
    def remove_files(files: list) -> None:
        for file_name in files:
            file_path: Path = Path(file_name)
            if not file_path.is_file():
                continue
            file_path.unlink()

    @staticmethod
    def get_concatenated_name(linked_fastq_name: str) -> str:
        """ "create a name for the concatenated file for some read files"""
        return f"concatenated_{'_'.join(linked_fastq_name.split('_')[-4:])}"

    @staticmethod
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

    @staticmethod
    def parse_file_data(fastq_path: Path) -> FastqFileMeta:
        header_line: str = read_gzip_first_line(file_path=fastq_path)
        fastq_file_meta: FastqFileMeta = FastqHandler.parse_fastq_header(header_line)
        fastq_file_meta.path = fastq_path
        fastq_file_meta.undetermined = _is_undetermined_in_path(fastq_path)
        matches = re.findall(r"-l[1-9]t([1-9]{2})_", str(fastq_path))
        if len(matches) > 0:
            fastq_file_meta.flow_cell_id = f"{fastq_file_meta.flow_cell_id}-{matches[0]}"
        return fastq_file_meta

    @staticmethod
    def create_fastq_name(
        lane: int,
        flow_cell: str,
        sample: str,
        read_direction: int,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: str | None = None,
        meta: str | None = None,
    ) -> str:
        """Name a FASTQ file with standard conventions and
        no naming constrains from the workflow."""
        flow_cell: str = f"{flow_cell}-undetermined" if undetermined else flow_cell
        date: str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date}_{flow_cell}_{sample}_{index}_{read_direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"


class BalsamicFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: int,
        flow_cell: str,
        sample: str,
        read_direction: int,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: str | None = None,
        meta: str | None = None,
    ) -> str:
        """Name a FASTQ file following Balsamic conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        flow_cell = f"{flow_cell}-undetermined" if undetermined else flow_cell
        date: str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date}_{flow_cell}_{sample}_{index}_R_{read_direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"


class MipFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: int,
        flow_cell: str,
        sample: str,
        read_direction: int,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: str | None = None,
        meta: str | None = None,
    ) -> str:
        """Name a FASTQ file following MIP conventions."""
        flow_cell = f"{flow_cell}-undetermined" if undetermined else flow_cell
        date: str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date}_{flow_cell}_{sample}_{index}_{read_direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"


class MicrosaltFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: int,
        flow_cell: str,
        sample: str,
        read_direction: int,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: str | None = None,
        meta: str | None = None,
    ) -> str:
        """Name a FASTQ file following usalt conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        flow_cell = f"{flow_cell}-undetermined" if undetermined else flow_cell
        return f"{sample}_{flow_cell}_L{lane}_{read_direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"


class MutantFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: int,
        flow_cell: str,
        sample: str,
        read_direction: int,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: str | None = None,
        meta: str | None = None,
    ) -> str:
        """Name a FASTQ file following mutant conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        return f"{flow_cell}_L{lane}_{meta}_{read_direction}{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    @staticmethod
    def get_concatenated_name(linked_fastq_name: str) -> str:
        """ "Create a name for the concatenated file from multiple lanes"""
        return "_".join(linked_fastq_name.split("_")[2:])

    @staticmethod
    def get_nanopore_header_info(line: str) -> dict:
        fastq_meta = {"flowcell": None}
        header_metadata: list = line.split(" ")
        flowcell = header_metadata[5].split("=")
        fastq_meta["flowcell"] = flowcell[1]
        return fastq_meta

    @staticmethod
    def create_nanopore_fastq_name(
        flowcell: str,
        sample: str,
        filenr: str,
        meta: str | None = None,
    ) -> str:
        return f"{flowcell}_{sample}_{meta}_{filenr}{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    @staticmethod
    def parse_nanopore_file_data(fastq_path: Path) -> dict:
        with gzip.open(fastq_path) as handle:
            header_line = handle.readline().decode()
            header_info: dict = MutantFastqHandler.get_nanopore_header_info(line=header_line)
            data = {
                "path": fastq_path,
                "flowcell": header_info["flowcell"],
            }
            return data
