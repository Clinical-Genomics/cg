"""
    Module for compressing BAM to CRAM
"""

import json
import logging
from pathlib import Path
from pprint import pprint as pp
from typing import List

from marshmallow import ValidationError

from cg.constants import (
    BAM_INDEX_SUFFIX,
    BAM_SUFFIX,
    CRAM_INDEX_SUFFIX,
    CRAM_SUFFIX,
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
    SPRING_SUFFIX,
)
from cg.utils import Process
from cg.utils.date import get_date_str

from .models import CrunchyFileSchema
from .sbatch import (
    SBATCH_BAM_TO_CRAM,
    SBATCH_FASTQ_TO_SPRING,
    SBATCH_HEADER_TEMPLATE,
    SBATCH_SPRING_TO_FASTQ,
)

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
        self.ntasks = 12
        self.mem = 50
        self.time = 24

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run

    # These are the compression/decompression methods
    def bam_to_cram(self, bam_path: Path):
        """
            Compress BAM file into CRAM
        """
        cram_path = self.get_cram_path_from_bam(bam_path)
        job_name = bam_path.name + "_bam_to_cram"
        flag_path = self.get_flag_path(file_path=cram_path)
        pending_path = self.get_pending_path(file_path=bam_path)
        log_dir = self.get_log_dir(bam_path)

        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=log_dir)

        sbatch_body = self._get_slurm_bam_to_cram(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            pending_path=pending_path,
            reference_path=self.reference_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        sbatch_path = self.get_sbatch_path(log_dir, "bam")
        self._submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def fastq_to_spring(self, fastq_first: Path, fastq_second: Path):
        """
            Compress FASTQ files into SPRING by sending to sbatch SLURM
        """
        spring_path = self.get_spring_path_from_fastq(fastq=fastq_first)
        job_name = str(fastq_first.name).replace(FASTQ_FIRST_READ_SUFFIX, "_fastq_to_spring")
        flag_path = self.get_flag_path(file_path=spring_path)
        pending_path = self.get_pending_path(file_path=fastq_first)
        log_dir = self.get_log_dir(spring_path)

        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=log_dir)

        sbatch_body = self._get_slurm_fastq_to_spring(
            fastq_first_path=fastq_first,
            fastq_second_path=fastq_second,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        sbatch_path = self.get_sbatch_path(log_dir, "fastq")
        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def spring_to_fastq(self, spring_path: Path):
        """
            Decompress SPRING into fastq by sending to sbatch SLURM
        """
        metadata_file = self.get_flag_path(spring_path)
        spring_metadata = self.get_spring_metadata(metadata_file)
        files_info = self.get_spring_archive_files(spring_metadata)

        fastq_first_path = Path(files_info["fastq_first"]["path"])

        job_name = str(fastq_first_path.name).replace(FASTQ_FIRST_READ_SUFFIX, "_spring_to_fastq")
        pending_path = self.get_pending_path(file_path=fastq_first_path)
        log_dir = self.get_log_dir(spring_path)

        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=log_dir)

        sbatch_body = self._get_slurm_spring_to_fastq(
            fastq_first_path=str(fastq_first_path),
            fastq_second_path=files_info["fastq_second"]["path"],
            spring_path=spring_path,
            pending_path=pending_path,
            checksum_first=files_info["fastq_first"]["checksum"],
            checksum_second=files_info["fastq_second"]["checksum"],
        )

        sbatch_path = self.get_sbatch_path(log_dir, "spring")
        sbatch_content = "\n".join([sbatch_header, sbatch_body])
        self._submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    # Spring metadata methods
    def get_spring_metadata(self, metadata_path: Path) -> List[dict]:
        """Validate content of metadata file and return mapped content"""
        LOG.info("Fetch spring metadata from %s", metadata_path)
        with open(metadata_path, "r") as infile:
            content = json.load(infile)
            print("content")
            pp(content)
            assert isinstance(content, list)
            metadata = self.mapped_spring_metadata(content)
            print("metadata")
            pp(metadata)

        if not metadata:
            LOG.warning("Could not find any content in file %s", metadata_path)
            return None

        if len(metadata) != 3:
            LOG.warning("Wrong number of files in spring metada file: %s", metadata_path)
            LOG.info("Found %s files, should always be 3 files", len(metadata))
            return None

        return metadata

    def update_metadata_date(self, spring_metadata_path: Path) -> None:
        """Set date to today in the spring metadata file"""

        today_str = get_date_str(None)
        spring_metadata = self.get_spring_metadata(spring_metadata_path)
        if not spring_metadata:
            raise SyntaxError
        LOG.info("Adding todays date to spring metadata file")
        for file_info in spring_metadata:
            file_info["updated"] = today_str

        with open(spring_metadata_path, "w") as outfile:
            outfile.write(json.dumps(spring_metadata))

    @staticmethod
    def mapped_spring_metadata(metadata=List[dict]) -> List[dict]:
        """Validate the content of a spring metadata file and map them on the schema"""
        file_schema = CrunchyFileSchema(many=True)
        LOG.info("Validating spring metadata content")
        try:
            dumped_data = file_schema.load(metadata)
        except ValidationError as err:
            LOG.warning(err.messages)
            return None
        LOG.debug("Spring metadata content looks fine")
        return dumped_data

    @staticmethod
    def get_spring_archive_files(spring_metadata: List[dict]) -> dict:
        """Map the files in spring metadata to a dictionary

        Returns: {
                    "fastq_first" : {file_info},
                    "fastq_second" : {file_info},
                    "spring" : {file_info},
                  }
        """
        names_map = {"first_read": "fastq_first", "second_read": "fastq_second", "spring": "spring"}
        return {names_map[file_info["file"]]: file_info for file_info in spring_metadata}

    # Methods to check compression status
    def is_compression_pending(self, file_path: Path) -> bool:
        """Check if compression/decompression has started but not finished"""
        pending_path = self.get_pending_path(file_path)
        if pending_path.exists():
            LOG.info("Compression/decompression is pending for %s", file_path)
            return True
        return False

    def is_compression_possible(self, file_path: Path) -> bool:
        """Check if compression/decompression is possible"""
        if file_path is None or not file_path.exists():
            LOG.warning("Could not find file to work with %s", file_path)
            return False

        if self.is_compression_pending(file_path):
            return False

        file_type = self.get_file_type(file_path)
        if file_type == "bam" and self.is_cram_compression_done(file_path):
            LOG.info("cram compression already exists for %s", file_path)
            return False

        if file_type == "fastq" and self.is_spring_compression_done(file_path):
            LOG.info("SPRING compression already exists for %s", file_path)
            return False

        if file_type == "spring" and self.is_spring_decompression_done(file_path):
            LOG.info("Decompressed SPRING already exists for %s", file_path)
            return False

        return True

    def is_cram_compression_done(self, bam_path: Path) -> bool:
        """Check if CRAM compression already done for BAM file"""
        cram_path = self.get_cram_path_from_bam(bam_path)
        flag_path = self.get_flag_path(file_path=cram_path)

        if not cram_path.exists():
            LOG.info("No cram-file for %s", bam_path)
            return False
        index_paths = self.get_index_path(cram_path)
        index_single_suffix = index_paths["single_suffix"]
        index_double_suffix = index_paths["double_suffix"]
        if (not index_single_suffix.exists()) and (not index_double_suffix.exists()):
            LOG.info("No index-file for %s", cram_path)
            return False
        if not flag_path.exists():
            LOG.info("No %s file for %s", FLAG_PATH_SUFFIX, cram_path)
            return False
        return True

    def is_spring_compression_done(self, fastq_file: Path) -> bool:
        """Check if spring compression if finished"""
        spring_path = self.get_spring_path_from_fastq(fastq_file)
        LOG.info("Check is spring file %s exists", spring_path)

        if not spring_path.exists():
            LOG.info("No SPRING file for %s", fastq_file)
            return False

        flag_path = self.get_flag_path(file_path=spring_path)
        if not flag_path.exists():
            LOG.info("No %s file for %s", FLAG_PATH_SUFFIX, fastq_file)
            return False

        return True

    def is_spring_decompression_done(self, spring_path: Path) -> bool:
        """Check if spring decompression if finished.

        This means that all three files specified in spring metadata should exist
        """
        spring_metadata_path = self.get_flag_path(spring_path)
        LOG.info("Check if spring metadata file %s exists", spring_metadata_path)

        if not spring_metadata_path.exists():
            LOG.info("No SPRING metadata file for %s", spring_path)
            return False

        spring_metadata = self.get_spring_metadata(spring_metadata_path)
        if not spring_metadata:
            return False

        for file_info in spring_metadata:
            if not Path(file_info["path"]).exists():
                return False

        return True

    # Methods to get file information
    @staticmethod
    def get_log_dir(file_path: Path) -> Path:
        """Return the path to where logs should be stored"""
        return file_path.parent

    @staticmethod
    def get_sbatch_path(log_dir: Path, compression: str) -> Path:
        """Return the path to where sbatch should be printed"""
        if compression == "fastq":
            return log_dir / "compress_fastq.sh"
        if compression == "spring":
            return log_dir / "decompress_spring.sh"
        return log_dir / "compress_bam.sh"

    @staticmethod
    def get_file_type(file_path: Path) -> str:
        """Check what file type a file is depending on the file ending"""
        if str(file_path).endswith(SPRING_SUFFIX):
            return "spring"
        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return "fastq"
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return "fastq"
        if file_path.suffix == BAM_SUFFIX:
            return "bam"
        if file_path.suffix == CRAM_SUFFIX:
            return "cram"
        LOG.warning("Unknown file type")
        return None

    @staticmethod
    def get_flag_path(file_path):
        """Get path to 'finished' flag.
        When compressing fastq this means that a .json metadata file has been created
        Otherwise, for bam compression, a regular flag path is returned.
        """
        if str(file_path).endswith(SPRING_SUFFIX):
            return file_path.with_suffix("").with_suffix(".json")

        return file_path.with_suffix(FLAG_PATH_SUFFIX)

    @staticmethod
    def get_pending_path(file_path: Path) -> Path:
        """Gives path to pending-flag path

        The file ending can be either fastq, spring or bam. They are treated as shown below
        """
        if str(file_path).endswith(SPRING_SUFFIX):
            return Path(str(file_path).replace(SPRING_SUFFIX, PENDING_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_FIRST_READ_SUFFIX, PENDING_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_SECOND_READ_SUFFIX, PENDING_PATH_SUFFIX))
        return file_path.with_suffix(PENDING_PATH_SUFFIX)

    @staticmethod
    def get_index_path(file_path: Path) -> dict:
        """Get possible paths for index

        Returns:
            dict: path with single_suffix, e.g. .bai and path with double_suffix, e.g. .bam.bai
        """
        index_type = CRAM_INDEX_SUFFIX
        if file_path.suffix == BAM_SUFFIX:
            index_type = BAM_INDEX_SUFFIX
        with_single_suffix = file_path.with_suffix(index_type)
        with_double_suffix = file_path.with_suffix(file_path.suffix + index_type)
        return {
            "single_suffix": with_single_suffix,
            "double_suffix": with_double_suffix,
        }

    @staticmethod
    def get_cram_path_from_bam(bam_path: Path) -> Path:
        """ Get corresponding CRAM file path from bam file path """
        if not bam_path.suffix == BAM_SUFFIX:
            LOG.error("%s does not end with %s", bam_path, BAM_SUFFIX)
            raise ValueError
        cram_path = bam_path.with_suffix(CRAM_SUFFIX)
        return cram_path

    @staticmethod
    def get_spring_path_from_fastq(fastq: Path) -> Path:
        """ GET corresponding SPRING file path from a FASTQ file"""
        suffix = FASTQ_FIRST_READ_SUFFIX
        if FASTQ_SECOND_READ_SUFFIX in str(fastq):
            suffix = FASTQ_SECOND_READ_SUFFIX

        spring_path = Path(str(fastq).replace(suffix, "")).with_suffix(SPRING_SUFFIX)
        return spring_path

    def _submit_sbatch(self, sbatch_content: str, sbatch_path: Path):
        """Submit slurm job"""
        if self.dry_run:
            LOG.info("Would submit following to slurm:\n\n%s", sbatch_content)
            return
        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters = [str(sbatch_path.resolve())]
        self.process.run_command(sbatch_parameters)
        LOG.info(self.process.stderr)
        LOG.info(self.process.stdout)

    def _get_slurm_header(self, job_name: str, log_dir: str) -> str:
        """Create and return a header for a sbatch script"""
        LOG.info("Generating sbatch header")
        sbatch_header = SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            conda_env=self.crunchy_env,
            mail_user=self.mail_user,
            ntasks=self.ntasks,
            time=self.time,
            mem=self.mem,
        )
        return sbatch_header

    @staticmethod
    def _get_slurm_bam_to_cram(
        bam_path: str, cram_path: str, flag_path: str, pending_path: str, reference_path: str,
    ) -> str:
        """Create and return the body of a sbatch script that runs bam to cram"""
        LOG.info("Generating bam to fastq sbatch body")
        sbatch_body = SBATCH_BAM_TO_CRAM.format(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            pending_path=pending_path,
            reference_path=reference_path,
        )
        return sbatch_body

    @staticmethod
    def _get_slurm_fastq_to_spring(
        fastq_first_path: str,
        fastq_second_path: str,
        spring_path: str,
        flag_path: str,
        pending_path: str,
    ) -> str:
        """Create and return the body of a sbatch script that runs bam to cram"""
        LOG.info("Generating fastq to spring sbatch body")
        sbatch_body = SBATCH_FASTQ_TO_SPRING.format(
            fastq_first=fastq_first_path,
            fastq_second=fastq_second_path,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        return sbatch_body

    @staticmethod
    def _get_slurm_spring_to_fastq(
        fastq_first_path: str,
        fastq_second_path: str,
        spring_path: str,
        pending_path: str,
        checksum_first: str,
        checksum_second: str,
    ) -> str:
        """Create and return the body of a sbatch script that runs bam to cram"""
        LOG.info("Generating spring to fastq sbatch body")
        sbatch_body = SBATCH_SPRING_TO_FASTQ.format(
            spring_path=spring_path,
            fastq_first=fastq_first_path,
            fastq_second=fastq_second_path,
            pending_path=pending_path,
            checksum_first=checksum_first,
            checksum_second=checksum_second,
        )

        return sbatch_body
