"""API for transfer a flow cell."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from housekeeper.store.models import Bundle, Version, Tag, File
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.store import Store
from cg.store.models import Sample, Flowcell

LOG = logging.getLogger(__name__)


def _set_status_db_sample_sequenced_at(
    status_db_sample: Sample, flow_cell_sequenced_at: datetime
) -> None:
    """Set sequenced at for sample in status db."""
    is_newer_date: datetime = (status_db_sample.sequenced_at is None) or (
        flow_cell_sequenced_at > status_db_sample.sequenced_at
    )
    if is_newer_date:
        status_db_sample.sequenced_at: datetime = flow_cell_sequenced_at


def log_enough_reads(
    status_db_sample_reads: int, application_expected_reads: int, cgstats_sample_name: str
) -> None:
    """Check and log if sample in status db got enough reads."""
    enough_reads: bool = status_db_sample_reads > application_expected_reads
    LOG.info(f"Added reads to sample: {cgstats_sample_name} - {status_db_sample_reads} ")
    LOG.info(f"[{'DONE' if enough_reads else 'NOT DONE'}]")


class TransferFlowCell:
    """Transfer flow cell API."""

    def __init__(self, db: Store, stats_api: StatsAPI, hk_api: HousekeeperAPI):
        self.db: Store = db
        self.stats: StatsAPI = stats_api
        self.hk: HousekeeperAPI = hk_api

    def transfer(self, flow_cell_dir: Path, flow_cell_id: str, store: bool = True) -> Flowcell:
        """Populate the database with the information."""
        self._add_tags_to_housekeeper(
            store=store,
            tags=[
                SequencingFileTag.FASTQ,
                SequencingFileTag.SAMPLE_SHEET,
                flow_cell_id,
                SequencingFileTag.CGSTATS_LOG,
            ],
        )
        cgstats_flow_cell: StatsFlowcell = self.stats.flowcell(flowcell_name=flow_cell_id)
        flow_cell: Flowcell = self._add_flow_cell_to_status_db(
            cgstats_flow_cell=cgstats_flow_cell,
            flow_cell=self.db.get_flow_cell(flow_cell_id=flow_cell_id),
            flow_cell_id=flow_cell_id,
        )

        self._include_sample_sheet_to_housekeeper(
            flow_cell_dir=flow_cell_dir, flow_cell_id=flow_cell_id, store=store
        )
        self._include_cgstats_log_to_housekeeper(
            flow_cell_dir=flow_cell_dir, flow_cell_id=flow_cell_id, store=store
        )
        self._parse_flow_cell_samples(
            cgstats_flow_cell=cgstats_flow_cell,
            flow_cell=flow_cell,
            flow_cell_id=flow_cell_id,
            store=store,
        )
        return flow_cell

    def _add_tags_to_housekeeper(self, store: bool, tags: List[str]) -> None:
        """Add and commit tag(s) to Housekeeper if not already exists in database."""
        for tag in tags:
            if store and self.hk.tag(name=tag) is None:
                self.hk.add_commit(self.hk.new_tag(tag))

    def _parse_flow_cell_samples(
        self,
        cgstats_flow_cell: StatsFlowcell,
        flow_cell: Flowcell,
        flow_cell_id: str,
        store: bool,
    ) -> None:
        """Adds fastq to Housekeeper, set sequenced at for sample, add samples to flow cell."""
        for cgstats_sample in cgstats_flow_cell.samples:
            LOG.debug(f"Adding reads/FASTQs to sample: {cgstats_sample.name}")

            status_db_sample: Sample = self.db.sample(internal_id=cgstats_sample.name)

            if not status_db_sample:
                LOG.warning(f"Unable to find sample: {cgstats_sample.name}")
                continue

            if store:
                self._store_sequencing_files(
                    flow_cell_id=flow_cell_id,
                    sample_id=status_db_sample.internal_id,
                    sequencing_files=cgstats_sample.fastqs,
                    tag_name=SequencingFileTag.FASTQ,
                )

            status_db_sample.reads = cgstats_sample.reads

            _set_status_db_sample_sequenced_at(
                status_db_sample=status_db_sample, flow_cell_sequenced_at=flow_cell.sequenced_at
            )

            if isinstance(status_db_sample, Sample):
                flow_cell.samples.append(status_db_sample)

            log_enough_reads(
                status_db_sample_reads=status_db_sample.reads,
                application_expected_reads=status_db_sample.application_version.application.expected_reads,
                cgstats_sample_name=cgstats_sample.name,
            )

    def _add_flow_cell_to_status_db(
        self, cgstats_flow_cell: StatsFlowcell, flow_cell: Optional[Flowcell], flow_cell_id: str
    ) -> Flowcell:
        """Add a flow cell to the status database."""
        if not flow_cell:
            flow_cell: Flowcell = self.db.add_flow_cell(
                flow_cell_id=flow_cell_id,
                sequencer_name=cgstats_flow_cell.sequencer,
                sequencer_type=cgstats_flow_cell.sequencer_type,
                date=cgstats_flow_cell.date,
                flow_cell_status=FlowCellStatus.ONDISK,
            )
        return flow_cell

    def _include_sequencing_file(
        self, file_path: Path, flow_cell_id: str, store: bool, tag_name: str
    ) -> None:
        """Include sequencing file in housekeeper."""
        if not file_path.exists():
            LOG.warning(f"Unable to find file: {file_path.as_posix()}")
        elif store:
            self._store_sequencing_files(
                flow_cell_id=flow_cell_id,
                sequencing_files=[file_path.as_posix()],
                tag_name=tag_name,
            )

    def _include_sample_sheet_to_housekeeper(
        self, flow_cell_dir: Path, flow_cell_id: str, store: bool
    ) -> None:
        """Include sample sheet in Housekeeper."""
        sample_sheet_path: Path = Path(
            flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )
        self._include_sequencing_file(
            file_path=sample_sheet_path,
            flow_cell_id=flow_cell_id,
            store=store,
            tag_name=SequencingFileTag.SAMPLE_SHEET,
        )

    def _include_cgstats_log_to_housekeeper(
        self, flow_cell_dir: Path, flow_cell_id: str, store: bool
    ) -> None:
        """Include cgstats log in Housekeeper."""
        for cgstats_log_path in flow_cell_dir.glob("stats-*[0-9]-*"):
            self._include_sequencing_file(
                file_path=cgstats_log_path,
                flow_cell_id=flow_cell_id,
                store=store,
                tag_name=SequencingFileTag.CGSTATS_LOG,
            )

    def _check_if_sequencing_file_is_on_bundle(self, file: str, bundle: Bundle) -> bool:
        """Check if file name is already on bundle."""
        latest_version: Version = self.hk.get_latest_bundle_version(bundle_name=bundle.name)
        return any(
            Path(file).name == Path(bundle_file.path).name for bundle_file in latest_version.files
        )

    def _store_sequencing_files(
        self,
        flow_cell_id: str,
        sequencing_files: List[str],
        tag_name: str,
        sample_id: Optional[str] = None,
    ) -> None:
        """Store sequencing file(s) in Housekeeper."""
        bundle_name: str = sample_id or flow_cell_id
        hk_bundle: Optional[Bundle] = self.hk.bundle(bundle_name)
        if not hk_bundle:
            hk_bundle: Bundle = self.hk.create_new_bundle_and_version(name=bundle_name)

        with self.hk.session_no_autoflush():
            for file in sequencing_files:
                if self._check_if_sequencing_file_is_on_bundle(file=file, bundle=hk_bundle):
                    LOG.info(f"Found file: {file}.")
                    LOG.info("Skipping file")
                else:
                    LOG.info(f"Found new file: {file}.")
                    LOG.info(f"Adding file using tag: {tag_name}")
                    self.hk.add_and_include_file_to_latest_version(
                        bundle_name=bundle_name, file=Path(file), tags=[tag_name, flow_cell_id]
                    )
