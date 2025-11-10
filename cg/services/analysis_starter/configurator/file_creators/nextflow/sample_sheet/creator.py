import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.io.csv import write_csv
from cg.io.gzip import read_gzip_first_line
from cg.meta.workflow.fastq import is_undetermined_in_path
from cg.models.fastq import FastqFileMeta, GetFastqFileMeta
from cg.store.models import Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class NextflowFastqSampleSheetCreator(ABC):

    def __init__(self, housekeeper_api: HousekeeperAPI, store: Store):
        self.housekeeper_api = housekeeper_api
        self.store = store

    def create(self, case_id: str, file_path: Path) -> None:
        LOG.debug(f"Creating sample sheet for case {case_id}")
        content: list[list[str]] = self._get_content(case_id)
        write_csv(file_path=file_path, content=content)

    @abstractmethod
    def _get_content(self, case_id: str) -> list[list[str]]:
        pass

    def _get_paired_read_paths(self, sample: Sample) -> Iterator[tuple[str, str]]:
        """Return an iterator of tuples with paired fastq paths for the forward and reverse read."""
        sample_metadata: list[FastqFileMeta] = self._get_fastq_metadata_for_sample(sample)
        fastq_forward_read_paths: list[str] = self._extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self._extract_read_files(
            metadata=sample_metadata, forward_read=False
        )
        return zip(fastq_forward_read_paths, fastq_reverse_read_paths)

    def _get_fastq_metadata_for_sample(self, sample: Sample) -> list[FastqFileMeta]:
        """Return FASTQ metadata objects for all fastq files linked to a sample."""
        return [
            self._parse_fastq_data(hk_file.full_path)
            for hk_file in self.housekeeper_api.files(
                bundle=sample.internal_id, tags={SequencingFileTag.FASTQ}
            )
        ]

    def _parse_fastq_data(self, fastq_path: Path) -> FastqFileMeta:
        header_line: str = read_gzip_first_line(file_path=fastq_path)
        fastq_file_meta: FastqFileMeta = self._parse_fastq_header(header_line)
        fastq_file_meta.path = fastq_path
        fastq_file_meta.undetermined = is_undetermined_in_path(fastq_path)
        matches = re.findall(r"-l[1-9]t([1-9]{2})_", str(fastq_path))
        if len(matches) > 0:
            fastq_file_meta.flow_cell_id = f"{fastq_file_meta.flow_cell_id}-{matches[0]}"
        return fastq_file_meta

    @staticmethod
    def _parse_fastq_header(line: str) -> FastqFileMeta | None:
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
    def _extract_read_files(metadata: list[FastqFileMeta], forward_read: bool) -> list[str]:
        """Extract a list of fastq file paths for either forward or reverse reads."""
        read_direction: int = 1 if forward_read else 2
        sorted_metadata: list = sorted(metadata, key=lambda k: k.path)
        return [
            fastq_file.path
            for fastq_file in sorted_metadata
            if fastq_file.read_direction == read_direction
        ]
