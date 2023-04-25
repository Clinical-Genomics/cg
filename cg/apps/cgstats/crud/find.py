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
        LOG.debug("Search for support parameters with file %s", demux_results.results_dir)
        support_parameters_id: Optional[int] = Supportparams.exists(str(demux_results.results_dir))
        if support_parameters_id:
            LOG.debug("Found support parameters with id %s", support_parameters_id)
            return support_parameters_id
        LOG.debug("Could not find support parameters")
        return None

    def get_datasource_id(self, demux_results: DemuxResults) -> Optional[int]:
        """Fetch the datasource id for a certain run"""
        stats_path = {
            "bcl2fastq": demux_results.conversion_stats_path,
            "dragen": demux_results.demux_stats_path,
        }
        LOG.debug("Search for datasource with file %s", stats_path[demux_results.bcl_converter])
        datasource_id: Optional[int] = Datasource.exists(
            str(stats_path[demux_results.bcl_converter])
        )
        if datasource_id:
            LOG.debug("Found datasource with id %s", datasource_id)
            return datasource_id
        LOG.debug("Could not find datasource")
        return None

    def get_flowcell_id(self, flowcell_name: str) -> Optional[int]:
        LOG.debug("Search for flowcell %s", flowcell_name)
        flowcell_id: Optional[int] = Flowcell.exists(flowcell_name)
        if flowcell_id:
            LOG.debug("Found flowcell with id %s", flowcell_id)
            return flowcell_id
        LOG.debug("Could not find flowcell")
        return None

    def get_demux_id(self, flowcell_object_id: int, base_mask: str = "") -> Optional[int]:
        """Flowcell object id refers to a database object"""
        demux_id: Optional[int] = Demux.exists(flowcell_id=flowcell_object_id, basemask=base_mask)
        if demux_id:
            return demux_id
        return None

    def get_project_id(self, project_name: str) -> Optional[int]:
        project_id: Optional[int] = Project.exists(project_name=project_name)
        if project_id:
            return project_id
        return None

    def get_sample(self, sample_id: str):
        """Get a unique demux sample."""
        pattern = SAMPLE_PATTERN.format(sample_id)
        return Sample.query.filter(
            or_(Sample.samplename.like(pattern), Sample.samplename == sample_id)
        ).first()

    def get_sample_id(self, sample_id: str, barcode: str) -> Optional[int]:
        sample_id: Optional[int] = Sample.exists(sample_name=sample_id, barcode=barcode)
        if sample_id:
            return sample_id
        return None

    def get_unaligned_id(self, sample_id: int, demux_id: int, lane: int) -> Optional[int]:
        unaligned_id: Optional[int] = Unaligned.exists(
            sample_id=sample_id, demux_id=demux_id, lane=lane
        )
        if unaligned_id:
            return unaligned_id
        return None

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
