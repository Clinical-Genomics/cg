"""API for transfer a flow cell."""

import logging
from pathlib import Path
from typing import List

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cgstats.flowcell import StatsFlowcell
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class TransferFlowCell:
    """Transfer flow cell API."""

    def __init__(self, db: Store, stats_api: StatsAPI, hk_api: HousekeeperAPI):
        self.db: Store = db
        self.stats: StatsAPI = stats_api
        self.hk: HousekeeperAPI = hk_api

    def transfer(self, flow_cell_id: str, store: bool = True) -> models.Flowcell:
        """Populate the database with the information."""
        if store and self.hk.tag("fastq") is None:
            self.hk.add_commit(self.hk.new_tag("fastq"))
        if store and self.hk.tag("samplesheet") is None:
            self.hk.add_commit(self.hk.new_tag("samplesheet"))
        if store and self.hk.tag(flow_cell_id) is None:
            self.hk.add_commit(self.hk.new_tag(flow_cell_id))
        stats_data: StatsFlowcell = self.stats.flowcell(flow_cell_id)
        flow_cell: models.Flowcell = self.db.flowcell(flow_cell_id)

        if flow_cell is None:
            flow_cell: models.Flowcell = self.db.add_flowcell(
                name=flow_cell_id,
                sequencer=stats_data.sequencer,
                sequencer_type=stats_data.sequencer_type,
                date=stats_data.date,
            )
        flow_cell.status = "ondisk"

        sample_sheet_path = self._sample_sheet_path(flow_cell_id)
        if not Path(sample_sheet_path).exists():
            LOG.warning(f"unable to find samplesheet: {sample_sheet_path}")
        elif store:
            self.store_samplesheet(flow_cell_id, sample_sheet_path)

        for sample_data in stats_data.samples:
            LOG.debug(f"adding reads/fastqs to sample: {sample_data.name}")
            sample_obj = self.db.sample(sample_data.name)
            if sample_obj is None:
                LOG.warning(f"unable to find sample: {sample_data.name}")
                continue

            if store:
                self.store_fastqs(
                    sample=sample_obj.internal_id,
                    flow_cell_id=flow_cell_id,
                    fastq_files=sample_data.fastqs,
                )

            sample_obj.reads = sample_data.reads
            enough_reads = (
                sample_obj.reads > sample_obj.application_version.application.expected_reads
            )
            newest_date = (sample_obj.sequenced_at is None) or (
                flow_cell.sequenced_at > sample_obj.sequenced_at
            )
            if newest_date:
                sample_obj.sequenced_at = flow_cell.sequenced_at

            if isinstance(sample_obj, models.Sample):
                flow_cell.samples.append(sample_obj)

            LOG.info(
                f"added reads to sample: {sample_data.name} - {sample_data.reads} "
                f"[{'DONE' if enough_reads else 'NOT DONE'}]"
            )

        return flow_cell

    def store_fastqs(self, sample: str, flow_cell_id: str, fastq_files: List[str]):
        """Store FASTQ files for a sample in Housekeeper."""
        hk_bundle = self.hk.bundle(sample)
        if hk_bundle is None:
            hk_bundle = self.hk.new_bundle(sample)
            self.hk.add_commit(hk_bundle)
            new_version = self.hk.new_version(created_at=hk_bundle.created_at)
            hk_bundle.versions.append(new_version)
            self.hk.commit()
            LOG.info(f"added new Housekeeper bundle: {hk_bundle.name}")

        with self.hk.session_no_autoflush():
            hk_version = hk_bundle.versions[0]
            for fastq_file in fastq_files:
                if self.hk.files(path=fastq_file).first() is None:
                    LOG.info(f"found FASTQ file: {fastq_file}")
                    tags = [self.hk.tag("fastq"), self.hk.tag(flow_cell_id)]
                    new_file = self.hk.new_file(path=fastq_file, tags=tags)
                    hk_version.files.append(new_file)
            self.hk.commit()

    def store_samplesheet(self, flow_cell_id: str, sample_sheet_path: str):
        """Store samplesheet for a run in Housekeeper"""
        hk_bundle = self.hk.bundle(flow_cell_id)
        if hk_bundle is None:
            hk_bundle = self.hk.new_bundle(flow_cell_id)
            self.hk.add_commit(hk_bundle)
            new_version = self.hk.new_version(created_at=hk_bundle.created_at)
            hk_bundle.versions.append(new_version)
            self.hk.commit()
            LOG.info(f"added new Housekeeper bundle: {hk_bundle.name}")

        with self.hk.session_no_autoflush():
            hk_version = hk_bundle.versions[0]
            if self.hk.files(path=sample_sheet_path).first() is None:
                LOG.info(f"Adding samplesheet: {sample_sheet_path}")
                tags = [self.hk.tag("samplesheet"), self.hk.tag(flow_cell_id)]
                new_file = self.hk.new_file(path=sample_sheet_path, tags=tags)
                hk_version.files.append(new_file)
        self.hk.commit()

    def _sample_sheet_path(self, flow_cell_id: str) -> str:
        """Construct the path to the samplesheet to be stored."""
        run_name: str = self.stats.run_name(flow_cell_id)
        document_path: str = self.stats.document_path(flow_cell_id)
        unaligned_dir: str = Path(document_path).name
        root_dir: Path = self.stats.root_dir
        return str(root_dir.joinpath(run_name, unaligned_dir, "SampleSheet.csv"))
