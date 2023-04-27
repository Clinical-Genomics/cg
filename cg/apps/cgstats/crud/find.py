import logging
from typing import List, Optional

import alchy
from sqlalchemy import or_

from cg.apps.cgstats.db.models import (
    Supportparams,
    Datasource,
    Demux,
    Flowcell,
    Project,
    Sample,
    Unaligned,
)
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults

LOG = logging.getLogger(__name__)
SAMPLE_PATTERN = "{}\_%"


class FindHandler:
    def get_support_parameters_id(self, demux_results: DemuxResults) -> Optional[int]:
        """Fetch the id of the support parameters if post exists"""
        LOG.debug(f"Search for support parameters with file {demux_results.results_dir}")

        support_parameters: Supportparams = self.get_support_parameters_by_document_path(
            document_path=str(demux_results.results_dir)
        )

        if support_parameters:
            support_parameters_id = support_parameters.supportparams_id
            LOG.debug(f"Found support parameters with id {support_parameters_id}")
            return support_parameters_id

        LOG.debug("Could not find support parameters")
        return None

    def get_support_parameters_by_document_path(
        self, document_path: str
    ) -> Optional[Supportparams]:
        return Supportparams.query.filter_by(document_path=document_path).first()

    def get_datasource_id(self, demux_results: DemuxResults) -> Optional[int]:
        """Fetch the datasource id for a certain run"""
        stats_path = {
            "bcl2fastq": demux_results.conversion_stats_path,
            "dragen": demux_results.demux_stats_path,
        }
        document_path: str = str(stats_path[demux_results.bcl_converter])
        LOG.debug(f"Search for datasource with file {document_path}")
        datasource: Datasource = self.get_datasource_by_document_path(document_path=document_path)

        if datasource:
            LOG.debug(f"Found datasource with id {datasource.datasource_id}")
            return datasource.datasource_id

        LOG.debug("Could not find datasource")
        return None

    def get_datasource_by_document_path(self, document_path: str) -> Optional[Datasource]:
        return Datasource.query.filter_by(document_path=document_path).first()

    def get_flowcell_id(self, flowcell_name: str) -> Optional[int]:
        LOG.debug(f"Search for flowcell {flowcell_name}")

        flowcell: Flowcell = self.get_flowcell_by_name(flowcell_name=flowcell_name)
        if flowcell:
            LOG.debug(f"Found flowcell with id {flowcell.flowcell_id}")
            return flowcell.flowcell_id

        LOG.debug("Could not find flowcell")
        return None

    def get_flowcell_by_name(self, flowcell_name: str):
        return Flowcell.query.filter_by(flowcellname=flowcell_name).first()

    def get_demux_id(self, flowcell_object_id: int, base_mask: str = "") -> Optional[int]:
        """Flowcell object id refers to a database object"""
        demux: Demux = self.get_demux_by_flowcell_id_and_base_mask(
            flowcell_id=flowcell_object_id, base_mask=base_mask
        )
        if demux:
            return demux.demux_id
        return None

    def get_demux_by_flowcell_id_and_base_mask(
        self, flowcell_id: int, base_mask: str
    ) -> Optional[Demux]:
        return Demux.query.filter_by(flowcell_id=flowcell_id).filter_by(basemask=base_mask).first()

    def get_project_id(self, project_name: str) -> Optional[int]:
        project: Project = self.get_project_by_name(project_name=project_name)

        if project:
            return project.project_id
        return None

    def get_project_by_name(self, project_name: str) -> Optional[Project]:
        return Project.query.filter_by(projectname=project_name).first()

    def get_sample(self, sample_id: str):
        """Get a unique demux sample."""
        pattern = SAMPLE_PATTERN.format(sample_id)
        return Sample.query.filter(
            or_(Sample.samplename.like(pattern), Sample.samplename == sample_id)
        ).first()

    def get_sample_id(self, sample_id: str, barcode: str) -> Optional[int]:
        sample: Sample = self.get_sample_by_name_and_barcode(sample_name=sample_id, barcode=barcode)
        if sample:
            return sample.sample_id
        return None

    def get_sample_by_name_and_barcode(self, sample_name: str, barcode: str) -> Optional[Sample]:
        return Sample.query.filter_by(samplename=sample_name).filter_by(barcode=barcode).first()

    def get_unaligned_id(self, sample_id: int, demux_id: int, lane: int) -> Optional[int]:
        unaligned: Unaligned = self.get_unaligned_by_sample_id_demux_id_and_lane(
            sample_id=sample_id, demux_id=demux_id, lane=lane
        )
        if unaligned:
            return unaligned.unaligned_id

    def get_unaligned_by_sample_id_demux_id_and_lane(
        self, sample_id: int, demux_id: int, lane: int
    ) -> Optional[Unaligned]:
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
