"""
This module handles concatenation of balsamic fastq files.

Classes:
    FastqFileNameCreator: Creates valid balsamic filenames
    FastqFileConcatenator: Handles file concatenation
    FastqHandler: Handles fastq file linking
"""
import logging
import os
import shutil
from pathlib import Path
from typing import List

from cg.apps.pipelines.fastqhandler import BaseFastqHandler

LOGGER = logging.getLogger(__name__)


class FastqFileConcatenator:
    """Concatenates a list of files into one"""

    @staticmethod
    def concatenate(files: List, concat_file):
        """Concatenates a list of fastq files"""
        LOGGER.info(FastqFileConcatenator.display_files(files, concat_file))

        with open(concat_file, "wb") as wfd:
            for fil in files:
                with open(fil, "rb") as file_descriptor:
                    shutil.copyfileobj(file_descriptor, wfd)

        size_before = FastqFileConcatenator().size_before(files)
        size_after = FastqFileConcatenator().size_after(concat_file)

        try:
            FastqFileConcatenator().assert_file_sizes(size_before, size_after)
        except AssertionError as error:
            LOGGER.warning(error)

    @staticmethod
    def size_before(files: List):
        """returns the total size of the linked fastq files before concatenation"""

        return sum([os.stat(f).st_size for f in files])

    @staticmethod
    def size_after(concat_file):
        """returns the size of the concatenated fastq files"""

        return os.stat(concat_file).st_size

    @staticmethod
    def assert_file_sizes(size_before, size_after):
        """asserts the file sizes before and after concatenation. If the file sizes differ by more
        than 1 percent, throw an exception"""
        msg = (
            f"Warning: Large file size difference after concatenation!"
            f"Before: {size_before} -> after: {size_after}"
        )

        assert abs(size_before - size_after) / size_before <= 0.01, msg
        LOGGER.info("Concatenation file size check successful!")

    @staticmethod
    def display_files(files: List, concat_file):
        """display file names for logging purposes"""

        concat_file_name = Path(concat_file).name
        msg = (
            f"Concatenating: {', '.join(Path(file_).name for file_ in files)} -> "
            f"{concat_file_name}"
        )

        return msg


class FastqHandler(BaseFastqHandler):
    """Handles fastq file linking"""

    class FastqFileNameCreator(BaseFastqHandler.BaseFastqFileNameCreator):
        """Creates valid balsamic filename from the parameters"""

        @staticmethod
        def create(lane: str, flowcell: str, sample: str, read: str, more: dict = None):
            """Name a FASTQ file following Balsamic conventions. Naming must be
            xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""
            date = more.get("date", None)
            index = more.get("index", None)
            undetermined = more.get("undetermined", None)

            flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
            date_str = date.strftime("%y%m%d") if date else "171015"
            index = index if index else "XXXXXX"
            return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_R_{read}.fastq.gz"

        @staticmethod
        def get_concatenated_name(linked_fastq_name):
            """"create a name for the concatenated file for some read files"""
            return f"concatenated_{'_'.join(linked_fastq_name.split('_')[-4:])}"

    def __init__(self, config):
        super().__init__(config)
        self.root_dir = config["balsamic"]["root"]

    def link(self, case: str, sample: str, files: List[dict]):
        """Link FASTQ files for a balsamic sample.
        Shall be linked to /<balsamic root directory>/case-id/fastq/"""

        wrk_dir = Path(f"{self.root_dir}/{case}/fastq")

        wrk_dir.mkdir(parents=True, exist_ok=True)

        linked_reads_paths = {1: [], 2: []}
        concatenated_paths = {1: "", 2: ""}

        sorted_files = sorted(files, key=lambda k: k["path"])

        for fastq_data in sorted_files:
            original_fastq_path = Path(fastq_data["path"])
            linked_fastq_name = self.FastqFileNameCreator.create(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample,
                read=fastq_data["read"],
                more={"undetermined": fastq_data["undetermined"]},
            )
            concatenated_fastq_name = self.FastqFileNameCreator.get_concatenated_name(
                linked_fastq_name
            )

            linked_fastq_path = wrk_dir / linked_fastq_name

            linked_reads_paths[fastq_data["read"]].append(linked_fastq_path)
            concatenated_paths[fastq_data["read"]] = f"{wrk_dir}/{concatenated_fastq_name}"

            if not linked_fastq_path.exists():
                LOGGER.info("linking: %s -> %s", original_fastq_path, linked_fastq_path)
                linked_fastq_path.symlink_to(original_fastq_path)
            else:
                LOGGER.debug("destination path already exists: %s", linked_fastq_path)

        LOGGER.info("Concatenation in progress for sample %s.", sample)
        for read in linked_reads_paths:
            FastqFileConcatenator().concatenate(linked_reads_paths[read], concatenated_paths[read])
            self._remove_files(linked_reads_paths[read])

    @staticmethod
    def _remove_files(files):
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

    @staticmethod
    def parse_header(line):
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
