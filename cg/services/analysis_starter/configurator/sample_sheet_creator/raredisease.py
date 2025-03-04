import logging
import re
from pathlib import Path

import rich_click as click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions, SequencingFileTag
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.io.csv import write_csv
from cg.io.gzip import read_gzip_first_line
from cg.meta.workflow.fastq import _is_undetermined_in_path
from cg.models.fastq import FastqFileMeta, GetFastqFileMeta
from cg.models.raredisease.raredisease import (
    RarediseaseSampleSheetEntry,
    RarediseaseSampleSheetHeaders,
)
from cg.services.analysis_starter.configurator.file_creators.abstract import NextflowFileCreator
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store

HEADER: list[str] = RarediseaseSampleSheetHeaders.list()
LOG = logging.getLogger(__name__)


class RarediseaseSampleSheetCreator(NextflowFileCreator):

    def __init__(self, store: Store, housekeeper_api: HousekeeperAPI):
        self.housekeeper_api = housekeeper_api
        self.store = store

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """Path to sample sheet."""
        return NextflowFileCreator._get_sample_sheet_path(case_id=case_id, case_path=case_path)

    def create(self, case_id: str, case_path: Path, dry_run: bool = False) -> None:
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: list[list[any]] = self._get_file_content(case_id=case_id)
        self._write_content_to_file_or_stdout(content=content, file_path=file_path, dry_run=dry_run)

    def _get_file_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        sample_sheet_content: list = []
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        fastq_forward_read_paths, fastq_reverse_read_paths = self._get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=case_sample.sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=self._get_sex_code(case_sample.sample.sex),
            phenotype=self._get_phenotype_code(case_sample.status),
            paternal_id=case_sample.get_paternal_sample_id,
            maternal_id=case_sample.get_maternal_sample_id,
            case_id=case_sample.case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content

    def _get_paired_read_paths(self, sample: Sample) -> tuple[list[str], list[str]]:
        """Returns a tuple of paired fastq file paths for the forward and reverse read."""
        sample_metadata: list[FastqFileMeta] = self._get_fastq_metadata_for_sample(sample)
        fastq_forward_read_paths: list[str] = self._extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self._extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        return fastq_forward_read_paths, fastq_reverse_read_paths

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
        fastq_file_meta.undetermined = _is_undetermined_in_path(fastq_path)
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
    def _extract_read_files(
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

    @staticmethod
    def _get_phenotype_code(phenotype: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to integer code")
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def _get_sex_code(sex: str) -> int:
        """Return Raredisease sex code."""
        LOG.debug("Translate sex to integer code")
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code

    @staticmethod
    def _write_content_to_file_or_stdout(
        content: list[list[any]], file_path: Path, dry_run: bool = False
    ) -> None:
        """Write sample sheet to file."""
        content.insert(0, HEADER)
        if dry_run:
            LOG.info(f"Dry-run: printing content to stdout. Would have written to {file_path}")
            click.echo(content)
            return
        LOG.debug(f"Writing sample sheet to {file_path}")
        write_csv(content=content, file_path=file_path)
