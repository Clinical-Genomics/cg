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
from typing import List, Optional


LOG = logging.getLogger(__name__)

DEFAULT_DATE_STR = (
    "171015"  # Stand in value to use if sequencing date cannot be extracted from header
)
DEFAULT_INDEX = (
    "XXXXXX"  # Stand in value to use if flowcell index is to be masked when renaming file
)


class FastqHandler:
    """Handles fastq file linking"""

    @staticmethod
    def concatenate(files: List, concat_file: str):
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
    def size_before(files: List) -> int:
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
    def display_files(files: List, concat_file: str) -> str:
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
    def parse_header(line: str) -> dict:
        """Generates a dict with parsed lanes, flowcells and read numbers
        Handle illumina's two different header formats
        @see https://en.wikipedia.org/wiki/FASTQ_format

        @HWUSI-EAS100R:6:73:941:1973#0/1

            HWUSI-EAS100R   the unique instrument name
            6   flowcell lane
            73  tile number within the flowcell lane
            941     'x'-coordinate of the cluster within the tile
            1973    'y'-coordinate of the cluster within the tile
            #0  index number for a multiplexed sample (0 for no indexing)
            /1  the member of a pair, /1 or /2 (paired-end or mate-pair reads only)

        Versions of the Illumina pipeline since 1.4 appear to use #NNNNNN
        instead of #0 for the multiplex ID, where NNNNNN is the sequence of the
        multiplex tag.

        With Casava 1.8 the format of the '@' line has changed:

        @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG

            EAS139  the unique instrument name
            136     the run id
            FC706VJ     the flowcell id
            2   flowcell lane
            2104    tile number within the flowcell lane
            15343   'x'-coordinate of the cluster within the tile
            197393  'y'-coordinate of the cluster within the tile
            1   the member of a pair, 1 or 2 (paired-end or mate-pair reads only)
            Y   Y if the read is filtered, N otherwise
            18  0 when none of the control bits are on, otherwise it is an even number
            ATCACG  index sequence
        """

        fastq_meta = {"lane": None, "flowcell": None, "readnumber": None}

        parts = line.split(":")
        if len(parts) == 5:  # @HWUSI-EAS100R:6:73:941:1973#0/1
            fastq_meta["lane"] = parts[1]
            fastq_meta["flowcell"] = "XXXXXX"
            fastq_meta["readnumber"] = parts[-1].split("/")[-1]
        if len(parts) == 10:  # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
            fastq_meta["lane"] = parts[3]
            fastq_meta["flowcell"] = parts[2]
            fastq_meta["readnumber"] = parts[6].split(" ")[-1]
        if len(parts) == 7:  # @ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1
            fastq_meta["lane"] = parts[3]
            fastq_meta["flowcell"] = parts[2]
            fastq_meta["readnumber"] = parts[-1].split("/")[-1]

        return fastq_meta

    @staticmethod
    def parse_file_data(fastq_path: Path) -> dict:
        with gzip.open(fastq_path) as handle:
            header_line = handle.readline().decode()
            header_info = FastqHandler.parse_header(header_line)

            data = {
                "path": fastq_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("Undetermined" in fastq_path),
            }
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", str(fastq_path))
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            return data

    @staticmethod
    def create_fastq_name(
        lane: str,
        flowcell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ):
        raise NotImplementedError


class BalsamicFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: str,
        flowcell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file following Balsamic conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_R_{read}.fastq.gz"


class MipFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: str,
        flowcell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file following MIP conventions."""
        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_{read}.fastq.gz"


class MicrosaltFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: str,
        flowcell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file following usalt conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz

        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        return f"{sample}_{flowcell}_L{lane}_{read}.fastq.gz"


class MutantFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: str,
        flowcell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file following mutant conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz

        return f"{flowcell}_L{lane}_{meta}_{read}.fastq.gz"

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
        meta: Optional[str] = None,
    ) -> str:
        return f"{flowcell}_{sample}_{meta}_{filenr}.fastq.gz"

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


class RnafusionFastqHandler(FastqHandler):
    @staticmethod
    def create_fastq_name(
        lane: str,
        flow_cell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file following MIP conventions,
        no naming constrains from pipeline."""
        flow_cell: str = f"{flow_cell}-undetermined" if undetermined else flow_cell
        date: str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date}_{flow_cell}_{sample}_{index}_{read}.fastq.gz"


class TaxprofilerFastqHandler(FastqHandler):
    """Handles Taxprofiler fastq file linking."""

    @staticmethod
    def create_fastq_name(
        lane: str,
        flow_cell: str,
        sample: str,
        read: str,
        date: dt.datetime = DEFAULT_DATE_STR,
        index: str = DEFAULT_INDEX,
        undetermined: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> str:
        """Name a FASTQ file, no naming constrains from pipeline."""
        flow_cell: str = f"{flow_cell}-undetermined" if undetermined else flow_cell
        date: str = date if isinstance(date, str) else date.strftime("%y%m%d")
        return f"{lane}_{date}_{flow_cell}_{sample}_{index}_{read}.fastq.gz"
