"""API for transfer a flow cell."""

import logging
from pathlib import Path
from typing import List, Dict, Optional

from housekeeper.store.models import Bundle, Version, Tag, File
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.store import Store, models
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class TransferFlowCell:
    """Transfer flow cell API."""

    def __init__(self, db: Store, stats_api: StatsAPI, hk_api: HousekeeperAPI):
        self.db: Store = db
        self.stats: StatsAPI = stats_api
        self.hk: HousekeeperAPI = hk_api

    def transfer(self, flow_cell_id: str, store: bool = True) -> models.Flowcell:
        """Populate the database with the information."""
        for tag in [SequencingFileTag.FASTQ, SequencingFileTag.SAMPLESHEET, flow_cell_id]:
            if store and self.hk.tag(name=tag) is None:
                self.hk.add_commit(self.hk.new_tag(tag))

        stats_data: StatsFlowcell = self.stats.flowcell(flow_cell_id)
        flow_cell: models.Flowcell = self.db.get_flow_cell(flow_cell_id)

        if flow_cell is None:
            flow_cell: models.Flowcell = self.db.add_flow_cell(
                flow_cell_id=flow_cell_id,
                sequencer_name=stats_data.sequencer,
                sequencer_type=stats_data.sequencer_type,
                date=stats_data.date,
                flow_cell_status=FlowCellStatus.ONDISK,
            )

        sample_sheet_path: Path = self._sample_sheet_path(flow_cell_id)
        if not sample_sheet_path.exists():
            LOG.warning(f"Unable to find sample sheet: {sample_sheet_path.as_posix()}")
        elif store:
            self._store_sequencing_file(
                flow_cell_id=flow_cell_id,
                sequencing_files=[sample_sheet_path.as_posix()],
                tag_name=SequencingFileTag.FASTQ,
            )

        for sample_data in stats_data.samples:
            LOG.debug(f"Adding reads/FASTQs to sample: {sample_data.name}")
            sample: Sample = self.db.sample(sample_data.name)
            if sample is None:
                LOG.warning(f"Unable to find sample: {sample_data.name}")
                continue

            if store:
                self._store_sequencing_file(
                    flow_cell_id=flow_cell_id,
                    sample_id=sample.internal_id,
                    sequencing_files=sample_data.fastqs,
                    tag_name=SequencingFileTag.FASTQ,
                )

            sample.reads = sample_data.reads
            enough_reads = sample.reads > sample.application_version.application.expected_reads
            newest_date = (sample.sequenced_at is None) or (
                flow_cell.sequenced_at > sample.sequenced_at
            )
            if newest_date:
                sample.sequenced_at = flow_cell.sequenced_at

            if isinstance(sample, models.Sample):
                flow_cell.samples.append(sample)

            LOG.info(
                f"Added reads to sample: {sample_data.name} - {sample_data.reads} "
                f"[{'DONE' if enough_reads else 'NOT DONE'}]"
            )
        return flow_cell

    def set_flow(self) -> models.Flowcell:
        """Set"""

    def _store_sequencing_file(
        self,
        flow_cell_id: str,
        sequencing_files: List[str],
        tag_name: str,
        sample_id: Optional[str] = None,
    ) -> None:
        """Stor sequencing file(s) in Housekeeper."""
        hk_bundle: Bundle = self.hk.bundle(sample_id) if sample_id else self.hk.bundle(flow_cell_id)
        if hk_bundle is None:
            hk_bundle: Bundle = self.hk.create_new_bundle_and_version(name=flow_cell_id)

        with self.hk.session_no_autoflush():
            hk_version: Version = hk_bundle.versions[0]
            for file in sequencing_files:
                if self.hk.files(path=file).first() is None:
                    LOG.info(f"Found new file: {file}.")
                    LOG.info(f"Adding file using tag: {tag_name}")
                    tags: List[Tag] = [self.hk.tag(name=tag_name), self.hk.tag(name=flow_cell_id)]
                    hk_version.files.append(self.hk.new_file(path=file, tags=tags))
            self.hk.commit()

    def _sample_sheet_path(self, flow_cell_id: str) -> Path:
        """Construct the path to the sample sheet to be stored."""
        run_name: str = self.stats.run_name(flow_cell_id)
        document_path: str = self.stats.document_path(flow_cell_id)
        unaligned_dir: str = Path(document_path).name
        root_dir: Path = self.stats.root_dir
        return root_dir.joinpath(
            run_name, unaligned_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )
