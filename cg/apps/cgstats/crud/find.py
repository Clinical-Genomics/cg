import logging
from pathlib import Path
from typing import Dict, List, Optional

import alchy
from sqlalchemy import or_

from cg.apps.cgstats.db.models import (
    Supportparams,
    Datasource,
    Demux,
    DemuxSample,
    DragenDemuxSample,
    Flowcell,
    Project,
    Sample,
    Unaligned,
)
from cg.apps.cgstats.parsers.conversion_stats import ConversionStats, SampleConversionResults
from cg.apps.cgstats.parsers.demux_stats import DemuxStats, SampleBarcodeStats
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample, SampleSheet
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults

LOG = logging.getLogger(__name__)
SAMPLE_PATTERN = "{}\_%"


class FindHandler:
    def get_support_parameters_by_document_path(
        self, document_path: str
    ) -> Optional[Supportparams]:
        """Get support parameters by document path."""

        LOG.debug(f"Searching for support parameters with file {document_path}")

        support_params: Supportparams = Supportparams.query.filter_by(
            document_path=document_path
        ).first()

        if support_params:
            LOG.debug(f"Found support parameters with id {support_params.supportparams_id}")
        else:
            LOG.debug("Support parameters not found")

        return support_params

    def get_datasource_by_document_path(self, document_path: str) -> Optional[Datasource]:
        """Get data source by document path."""
        LOG.debug(f"Search for datasource with file {document_path}")

        datasource: Datasource = Datasource.query.filter_by(document_path=document_path).first()

        if datasource:
            LOG.debug(f"Found datasource with id {datasource.datasource_id}")
        else:
            LOG.debug("Could not find datasource")

        return datasource

    def get_flow_cell_by_name(self, flow_cell_name: str) -> Optional[Flowcell]:
        """Get flow cell by name."""
        LOG.debug(f"Searching for flow cell {flow_cell_name}")

        flowcell: Flowcell = Flowcell.query.filter_by(flowcellname=flow_cell_name).first()

        if flowcell:
            LOG.debug(f"Found flow cell with id {flowcell.flowcell_id}")
        else:
            LOG.debug("Flow cell not found")

        return flowcell

    def get_demux_by_flow_cell_id_and_base_mask(
        self, flowcell_id: int, base_mask: str = ""
    ) -> Optional[Demux]:
        """Get demux by flow cell id and base mask."""
        return Demux.query.filter_by(flowcell_id=flowcell_id).filter_by(basemask=base_mask).first()

    def get_project_by_name(self, project_name: str) -> Optional[Project]:
        """Get project by name."""
        return Project.query.filter_by(projectname=project_name).first()

    def get_sample(self, sample_id: str):
        """Get a unique demux sample."""
        pattern = SAMPLE_PATTERN.format(sample_id)
        return Sample.query.filter(
            or_(Sample.samplename.like(pattern), Sample.samplename == sample_id)
        ).first()

    def get_sample_by_name_and_barcode(self, sample_name: str, barcode: str) -> Optional[Sample]:
        """Get sample by name and barcode."""
        return Sample.query.filter_by(samplename=sample_name).filter_by(barcode=barcode).first()

    def get_unaligned_by_sample_id_demux_id_and_lane(
        self, sample_id: int, demux_id: int, lane: int
    ) -> Optional[Unaligned]:
        """Get unaligned by sample id, demux id and lane."""
        return (
            Unaligned.query.filter_by(sample_id=sample_id)
            .filter_by(demux_id=demux_id)
            .filter_by(lane=lane)
            .first()
        )

    def get_samples(self, flowcell: str, project_name: Optional[str] = None) -> alchy.Query:
        query: alchy.Query = Sample.query.join(Sample.unaligned, Unaligned.demux, Demux.flowcell)
        if project_name:
            query = query.join(Sample.project).filter(Project.projectname == project_name)

        query = query.filter(Flowcell.flowcellname == flowcell)

        return query

    def project_sample_stats(
        self, flowcell: str, project_name: Optional[str] = None
    ) -> List[StatsSample]:
        samples_query: alchy.Query = self.get_samples(flowcell=flowcell, project_name=project_name)
        db_sample: Sample
        return [StatsSample.from_orm(db_sample) for db_sample in samples_query]

    def get_dragen_demux_samples(
        self,
        demux_results: DemuxResults,
        sample_sheet: SampleSheet,
    ) -> Dict[int, Dict[str, DragenDemuxSample]]:
        """Gather information from Dragen demultiplexing results and create samples with the correct
        information"""
        LOG.info("Gather post Dragen demultiplexing statistics for demultiplexed samples")
        demux_samples: Dict[int, Dict[str, DragenDemuxSample]] = {}

        for sample in sample_sheet.samples:
            if sample.lane not in demux_samples:
                demux_samples[sample.lane] = {}

            demultiplexing_stats = demux_results.demultiplexing_stats.parsed_stats[sample.lane][
                sample.sample_id
            ]

            quality_metrics = demux_results.quality_metrics.parsed_metrics[sample.lane][
                sample.sample_id
            ]

            adapter_metrics = demux_results.adapter_metrics.parsed_metrics[sample.lane][
                sample.sample_id
            ]

            demux_samples[sample.lane][sample.sample_id] = DragenDemuxSample(
                sample_name=sample.sample_id,
                flowcell=demux_results.flow_cell.id,
                lane=sample.lane,
                reads=int(demultiplexing_stats["# Reads"]),
                perfect_reads=int(demultiplexing_stats["# Perfect Index Reads"]),
                one_mismatch_reads=int(demultiplexing_stats["# One Mismatch Index Reads"]),
                pass_filter_q30=int(quality_metrics["YieldQ30"]),
                mean_quality_score=float(quality_metrics["Mean Quality Score (PF)"]),
                r1_sample_bases=int(adapter_metrics["R1_SampleBases"]),
                r2_sample_bases=int(adapter_metrics["R2_SampleBases"]),
                read_length=demux_results.run_info.mean_read_length(),
            )

        return demux_samples

    def get_demux_samples(
        self, conversion_stats: ConversionStats, demux_stats_path: Path, sample_sheet: SampleSheet
    ) -> Dict[int, Dict[str, DemuxSample]]:
        """Gather information from demultiplexing results and create samples with the correct
        information"""
        LOG.info("Gather post demultiplexing statistics for demultiplexed samples")
        demux_samples: Dict[int, Dict[str, DemuxSample]] = {}
        demux_stats: DemuxStats = DemuxStats(demux_stats_path=demux_stats_path)
        raw_clusters: Dict[int, int] = conversion_stats.raw_clusters_per_lane
        flowcell_id: str = conversion_stats.flowcell_id
        sample: FlowCellSample
        for sample in sample_sheet.samples:
            lane: int = sample.lane
            if lane not in demux_samples:
                demux_samples[lane] = {}
            barcode = "+".join([sample.index, sample.index2]) if sample.index2 else sample.index
            sample_barcode_stats: SampleBarcodeStats = demux_stats.lanes_to_barcode[lane][barcode]
            sample_conversion_stats: SampleConversionResults = conversion_stats.lanes_to_barcode[
                lane
            ][barcode]
            lane_raw_cluster: int = raw_clusters[lane]
            sample_id: str = sample.sample_id
            demux_samples[lane][sample_id] = DemuxSample(
                sample_name=sample.sample_id,
                flowcell=flowcell_id,
                lane=lane,
                nr_raw_clusters_=lane_raw_cluster,
                barcode_stats_=sample_barcode_stats,
                conversion_stats_=sample_conversion_stats,
            )

        return demux_samples
