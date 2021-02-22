"""
This module handles concatenation of balsamic fastq files.

Classes:
    FastqFileNameCreator: Creates valid balsamic filenames
    FastqHandler: Handles fastq file linking
"""
import gzip
import logging
import os
import re
import shutil
from pathlib import Path
from typing import List
import datetime as dt

LOG = logging.getLogger(__name__)


class FastqHandler:
    """Handles fastq file linking"""

    @staticmethod
    def concatenate(files: List, concat_file: str):
        """Concatenates a list of fastq files"""
        LOG.info(FastqHandler.display_files(files, concat_file))

        with open(concat_file, "wb") as wfd:
            for fil in files:
                with open(fil, "rb") as file_descriptor:
                    shutil.copyfileobj(file_descriptor, wfd)

        size_before = FastqHandler.size_before(files)
        size_after = FastqHandler.size_after(concat_file)

        try:
            FastqHandler.assert_file_sizes(size_before, size_after)
        except AssertionError as error:
            LOG.warning(error)

    @staticmethod
    def size_before(files: List) -> int:
        """returns the total size of the linked fastq files before concatenation"""

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
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

    @staticmethod
    def name_fastq_file(lane: str, flowcell: str, sample: str, read: str, more: dict = None) -> str:
        raise NotImplementedError

    @staticmethod
    def get_concatenated_name(linked_fastq_name) -> str:
        """"name_fastq_file a name for the concatenated file for some read files"""
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
    def link(sample_id: str, files: List[dict], concatenate: bool, working_dir: Path) -> None:
        """Link FASTQ files for a balsamic sample.
        Shall be linked to /<balsamic root directory>/case-id/fastq/"""

        working_dir.mkdir(parents=True, exist_ok=True)

        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: "", 2: ""}

        sorted_files = sorted(files, key=lambda k: k["path"])

        for fastq_data in sorted_files:
            original_fastq_path = Path(fastq_data["path"])
            linked_fastq_name = FastqHandler.name_fastq_file(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample_id,
                read=fastq_data["read"],
                more={"undetermined": fastq_data["undetermined"]},
            )

            linked_fastq_path = working_dir / linked_fastq_name

            linked_reads_paths[fastq_data["read"]].append(linked_fastq_path)
            concatenated_paths[
                fastq_data["read"]
            ] = f"{working_dir}/{FastqHandler.get_concatenated_name(linked_fastq_name)}"

            if not linked_fastq_path.exists():
                LOG.info("linking: %s -> %s", original_fastq_path, linked_fastq_path)
                linked_fastq_path.symlink_to(original_fastq_path)
            else:
                LOG.debug("destination path already exists: %s", linked_fastq_path)

        if not concatenate:
            return

        LOG.info("Concatenation in progress for sample %s.", sample_id)
        for read, value in linked_reads_paths.items():
            FastqHandler.concatenate(linked_reads_paths[read], concatenated_paths[read])
            FastqHandler.remove_files(value)

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
                "undetermined": ("_Undetermined_" in fastq_path),
            }
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", str(fastq_path))
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            return data


class BalsamicFastqHandler(FastqHandler):
    @staticmethod
    def name_fastq_file(lane: str, flowcell: str, sample: str, read: str, more: dict = None) -> str:
        """Name a FASTQ file following Balsamic conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
        date = more.get("date", None)
        index = more.get("index", None)
        undetermined = more.get("undetermined", None)

        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date.strftime("%y%m%d") if date else "171015"
        index = index or "XXXXXX"
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_R_{read}.fastq.gz"


class MipFastqHandler(FastqHandler):
    @staticmethod
    def name_fastq_file(
        lane: int,
        flowcell: str,
        sample: str,
        read: int,
        undetermined: bool = False,
        date: dt.datetime = None,
        index: str = None,
    ) -> str:
        """Name a FASTQ file following MIP conventions."""
        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date.strftime("%y%m%d") if date else "171015"
        index = index or "XXXXXX"
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_{read}.fastq.gz"
