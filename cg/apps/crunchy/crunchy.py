"""
    Module for interacting with crunchy to perform:
        1. Compressing: FASTQ to SPRING
        2. Decompressing: SPRING to FASTQ
    along with the helper methods
"""

import datetime
import json
import logging
import tempfile
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import List, Optional

from marshmallow import ValidationError

from cg.constants import FASTQ_DELTA
from cg.models import CompressionData
from cg.utils import Process
from cg.utils.date import get_date_str

from .models import CrunchyFileSchema
from .sbatch import SBATCH_FASTQ_TO_SPRING, SBATCH_HEADER_TEMPLATE, SBATCH_SPRING_TO_FASTQ

LOG = logging.getLogger(__name__)


FLAG_PATH_SUFFIX = ".crunchy.txt"
PENDING_PATH_SUFFIX = ".crunchy.pending.txt"


class CrunchyAPI:
    """
    API for crunchy
    """

    def __init__(self, config: dict):

        self.process = Process("sbatch")
        self.slurm_account = config["crunchy"]["slurm"]["account"]
        self.crunchy_env = config["crunchy"]["slurm"]["conda_env"]
        self.mail_user = config["crunchy"]["slurm"]["mail_user"]
        self.reference_path = config["crunchy"]["cram_reference"]
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Updating compress api")
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    # Methods to check compression status
    @staticmethod
    def is_compression_pending(compression_obj: CompressionData) -> bool:
        """Check if compression/decompression has started but not finished"""
        if compression_obj.pending_exists():
            LOG.info("Compression/decompression is pending for %s", compression_obj.run_name)
            return True
        LOG.info("Compression/decompression is not running")
        return False

    def is_fastq_compression_possible(self, compression_obj: CompressionData) -> bool:
        """Check if FASTQ compression is possible

        There are three possible answers to this question:

         - Compression is running          -> Compression NOT possible
         - SPRING archive exists           -> Compression NOT possible
         - Not compressed and not running  -> Compression IS possible
        """
        if self.is_compression_pending(compression_obj):
            return False

        if compression_obj.spring_exists():
            LOG.info("SPRING file found")
            return False

        LOG.info("FASTQ compression is possible")

        return True

    @staticmethod
    def is_spring_decompression_possible(compression_obj: CompressionData) -> bool:
        """Check if SPRING decompression is possible

        There are three possible answers to this question:

            - Compression/Decompression is running      -> Decompression is NOT possible
            - The FASTQ files are not compressed        -> Decompression is NOT possible
            - Compression has been performed            -> Decompression IS possible

        """
        if compression_obj.pending_exists():
            LOG.info("Compression/decompression is pending for %s", compression_obj.run_name)
            return False

        if not compression_obj.spring_exists():
            LOG.info("No SPRING file found")
            return False

        if compression_obj.pair_exists():
            LOG.info("FASTQ files already exists")
            return False

        LOG.info("Decompression is possible")

        return True

    def is_fastq_compression_done(self, compression_obj: CompressionData) -> bool:
        """Check if FASTQ compression is finished

        This is checked by controlling that the SPRING files that are produced after FASTQ
        compression exists.

        The following has to be fulfilled for FASTQ compression to be considered done:

            - A SPRING archive file exists
            - A SPRING archive metada file exists
            - The SPRING archive has not been unpacked before FASTQ delta (21 days)

        Note:
        'updated_at' indicates at what date the SPRING archive was unarchived last.
        If the SPRING archive has never been unarchived 'updated_at' is None

        """
        LOG.info("Check if FASTQ compression is finished")
        LOG.info("Check if SPRING file %s exists", compression_obj.spring_path)
        if not compression_obj.spring_exists():
            LOG.info("No SPRING file for %s", compression_obj.run_name)
            return False
        LOG.info("SPRING file found")

        LOG.info("Check if SPRING metadata file %s exists", compression_obj.spring_metadata_path)
        if not compression_obj.metadata_exists():
            LOG.info("No metadata file found")
            return False
        LOG.info("SPRING metadata file found")

        spring_metadata = self.get_spring_metadata(compression_obj.spring_metadata_path)
        # Check if the SPRING archive has been unarchived
        updated_at = self.get_file_updated_at(spring_metadata)

        if updated_at is None:
            LOG.info("FASTQ compression is done for %s", compression_obj.run_name)
            return True

        LOG.info("Files where unpacked %s", updated_at)

        if not self.check_if_update_spring(updated_at):
            return False

        LOG.info("FASTQ compression is done for %s", compression_obj.run_name)

        return True

    def is_spring_decompression_done(self, compression_obj: CompressionData) -> bool:
        """Check if SPRING decompression if finished.

        This means that all three files specified in SPRING metadata should exist.
        That is

            - First read in FASTQ pair should exist
            - Second read in FASTQ pair should exist
            - SPRING archive file should still exist
        """

        spring_metadata_path = compression_obj.spring_metadata_path
        LOG.info("Check if SPRING metadata file %s exists", spring_metadata_path)

        if not compression_obj.metadata_exists():
            LOG.info("No SPRING metadata file found")
            return False

        spring_metadata = self.get_spring_metadata(spring_metadata_path)
        if not spring_metadata:
            LOG.info("Malformed metadata content")
            return False

        for file_info in spring_metadata:
            if not Path(file_info["path"]).exists():
                LOG.info("File %s does not exist", file_info["path"])
                return False
            if "updated" not in file_info:
                LOG.info("Files have not been unarchived")
                return False

        LOG.info("SPRING decompression is done for run %s", compression_obj.run_name)

        return True

    # These are the compression/decompression methods
    def fastq_to_spring(self, compression_obj: CompressionData, sample_id: str = "") -> None:
        """
        Compress FASTQ files into SPRING by sending to sbatch SLURM

        """
        job_name = "_".join([sample_id, compression_obj.run_name, "fastq_to_spring"])

        log_dir = self.get_log_dir(compression_obj.spring_path)
        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=str(log_dir))

        sbatch_body = self._get_slurm_fastq_to_spring(compression_obj=compression_obj)
        sbatch_path = self.get_sbatch_path(log_dir, "fastq", compression_obj.run_name)
        sbatch_content = "\n".join([sbatch_header, sbatch_body])
        self._submit_sbatch(
            sbatch_content=sbatch_content,
            sbatch_path=sbatch_path,
            pending_path=compression_obj.pending_path,
        )

    def spring_to_fastq(self, compression_obj: CompressionData, sample_id: str = "") -> None:
        """
        Decompress SPRING into FASTQ by submitting sbatch script to SLURM

        """
        spring_metadata = self.get_spring_metadata(compression_obj.spring_metadata_path)

        job_name = "_".join([sample_id, compression_obj.run_name, "spring_to_fastq"])
        log_dir = self.get_log_dir(compression_obj.spring_path)

        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=str(log_dir))

        files_info = self.get_spring_archive_files(spring_metadata)

        sbatch_body = self._get_slurm_spring_to_fastq(
            compression_obj=compression_obj,
            checksum_first=files_info["fastq_first"]["checksum"],
            checksum_second=files_info["fastq_second"]["checksum"],
        )

        sbatch_path = self.get_sbatch_path(log_dir, "spring", compression_obj.run_name)
        sbatch_content = "\n".join([sbatch_header, sbatch_body])
        self._submit_sbatch(
            sbatch_content=sbatch_content,
            sbatch_path=sbatch_path,
            pending_path=compression_obj.pending_path,
        )

    # Spring metadata methods
    def get_spring_metadata(self, metadata_path: Path) -> Optional[List[dict]]:
        """Validate content of metadata file and return mapped content"""
        LOG.info("Fetch SPRING metadata from %s", metadata_path)
        with open(metadata_path, "r") as infile:
            try:
                content = json.load(infile)
            except JSONDecodeError:
                LOG.warning("No content in SPRING metadata file")
                return None
            assert isinstance(content, list)
            metadata = self.mapped_spring_metadata(content)

        if not metadata:
            LOG.warning("Could not find any content in file %s", metadata_path)
            return None

        if len(metadata) != 3:
            LOG.warning("Wrong number of files in SPRING metada file: %s", metadata_path)
            LOG.info("Found %s files, should always be 3 files", len(metadata))
            return None

        return metadata

    def update_metadata_date(self, spring_metadata_path: Path) -> None:
        """Update date in the SPRING metadata file to todays date"""

        today_str = get_date_str(None)
        spring_metadata = self.get_spring_metadata(spring_metadata_path)
        if not spring_metadata:
            raise SyntaxError
        LOG.info("Adding todays date to SPRING metadata file")
        for file_info in spring_metadata:
            file_info["updated"] = today_str

        with open(spring_metadata_path, "w") as outfile:
            outfile.write(json.dumps(spring_metadata))

    @staticmethod
    def mapped_spring_metadata(metadata=List[dict]) -> Optional[List[dict]]:
        """Validate the content of a SPRING metadata file and map them on the schema"""
        file_schema = CrunchyFileSchema(many=True)
        LOG.info("Validating SPRING metadata content")
        try:
            dumped_data = file_schema.load(metadata)
        except ValidationError as err:
            LOG.warning(err.messages)
            return None
        LOG.debug("Spring metadata content looks fine")
        return dumped_data

    @staticmethod
    def get_spring_archive_files(spring_metadata: List[dict]) -> dict:
        """Map the files in SPRING metadata to a dictionary

        Returns: {
                    "fastq_first" : {file_info},
                    "fastq_second" : {file_info},
                    "spring" : {file_info},
                  }
        """
        names_map = {"first_read": "fastq_first", "second_read": "fastq_second", "spring": "spring"}
        archive_files = {}
        for file_info in spring_metadata:
            file_name = names_map[file_info["file"]]
            archive_files[file_name] = file_info
        return archive_files

    @staticmethod
    def get_file_updated_at(spring_metadata: List[dict]) -> datetime.datetime:
        """Check if a SPRING metadata file has been updated and return the date when updated"""
        if "updated" not in spring_metadata[0]:
            return None
        return spring_metadata[0]["updated"]

    @staticmethod
    def check_if_update_spring(file_date: datetime.datetime) -> bool:
        """Check if date is older than FASTQ_DELTA (21 days)"""
        delta = file_date + datetime.timedelta(days=FASTQ_DELTA)
        now = datetime.datetime.now()
        if delta > now:
            LOG.info("FASTQ files are not old enough")
            return False
        return True

    # Methods to get file information
    @staticmethod
    def get_log_dir(file_path: Path) -> Path:
        """Return the path to where logs should be stored"""
        return file_path.parent

    @staticmethod
    def get_sbatch_path(log_dir: Path, compression: str, run_name: str = None) -> Path:
        """Return the path to where sbatch should be printed"""
        if compression == "fastq":
            return log_dir / "_".join([run_name, "compress_fastq.sh"])
        # Only other option is "SPRING"
        return log_dir / "_".join([run_name, "decompress_spring.sh"])

    def _submit_sbatch(self, sbatch_content: str, sbatch_path: Path, pending_path: Path):
        """Submit SLURM job"""
        LOG.info("Submit sbatch")
        if self.dry_run:
            LOG.info("Would submit sbatch %s to slurm", sbatch_path)
            return
        LOG.info("Creating pending flag")
        try:
            pending_path.touch(exist_ok=False)
        except FileExistsError:
            LOG.warning("Pending path exists! Do not submit batch job")
            return

        LOG.debug("Pending flag created")
        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters = [str(sbatch_path.resolve())]
        self.process.run_command(parameters=sbatch_parameters)
        if self.process.stderr:
            LOG.info(self.process.stderr)
        if self.process.stdout:
            LOG.info(self.process.stdout)

    def _get_slurm_header(self, job_name: str, log_dir: str) -> str:
        """Create and return a header for a sbatch script"""
        LOG.info("Generating sbatch header")
        ntasks = 12
        mem = 50
        time = 24
        sbatch_header = SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            conda_env=self.crunchy_env,
            mail_user=self.mail_user,
            ntasks=ntasks,
            time=time,
            mem=mem,
        )
        return sbatch_header

    @staticmethod
    def _get_tmp_dir(prefix: str, suffix: str, base: str = None) -> str:
        """Create a temporary directory and return the path to it"""

        with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=base) as dir_name:
            tmp_dir_path = dir_name

        LOG.info("Created temporary dir %s", tmp_dir_path)
        return tmp_dir_path

    @staticmethod
    def _get_slurm_fastq_to_spring(compression_obj: CompressionData) -> str:
        """Create and return the body of a sbatch script that runs FASTQ to SPRING"""
        LOG.info("Generating FASTQ to SPRING sbatch body")
        tmp_dir_path = CrunchyAPI._get_tmp_dir(
            prefix="spring_", suffix="_compress", base=compression_obj.analysis_dir
        )
        sbatch_body = SBATCH_FASTQ_TO_SPRING.format(
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            spring_path=compression_obj.spring_path,
            flag_path=compression_obj.spring_metadata_path,
            pending_path=compression_obj.pending_path,
            tmp_dir=tmp_dir_path,
        )

        return sbatch_body

    @staticmethod
    def _get_slurm_spring_to_fastq(
        compression_obj: CompressionData, checksum_first: str, checksum_second: str
    ) -> str:
        """Create and return the body of a sbatch script that runs SPRING to FASTQ"""
        LOG.info("Generating SPRING to FASTQ sbatch body")
        tmp_dir_path = CrunchyAPI._get_tmp_dir(
            prefix="spring_", suffix="_decompress", base=compression_obj.analysis_dir
        )
        sbatch_body = SBATCH_SPRING_TO_FASTQ.format(
            spring_path=compression_obj.spring_path,
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            pending_path=compression_obj.pending_path,
            checksum_first=checksum_first,
            checksum_second=checksum_second,
            tmp_dir=tmp_dir_path,
        )

        return sbatch_body
