import logging
from typing import List, Optional

import alchy
from cg.apps.cgstats.db import models
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.cgstats.stats_sample import StatsSample
from sqlalchemy import or_

LOG = logging.getLogger(__name__)
SAMPLE_PATTERN = "{}\_%"


def get_support_parameters_id(demux_results: DemuxResults) -> Optional[int]:
    """Fetch the id of the support parameters if post exists"""
    LOG.debug("Search for support parameters with file %s", demux_results.results_dir)
    support_parameters_id: Optional[int] = models.Supportparams.exists(
        str(demux_results.results_dir)
    )
    if support_parameters_id:
        LOG.debug("Found support parameters with id %s", support_parameters_id)
        return support_parameters_id
    LOG.debug("Could not find support parameters")
    return None


def get_datasource_id(demux_results: DemuxResults) -> Optional[int]:
    """Fetch the datasource id for a certain run"""
    LOG.debug("Search for datasource with file %s", demux_results.conversion_stats_path)
    datasource_id: Optional[int] = models.Datasource.exists(
        str(demux_results.conversion_stats_path)
    )
    if datasource_id:
        LOG.debug("Found datasource with id %s", datasource_id)
        return datasource_id
    LOG.debug("Could not find datasource")
    return None


def get_flowcell_id(flowcell_name: str) -> Optional[int]:
    LOG.debug("Search for flowcell %s", flowcell_name)
    flowcell_id: Optional[int] = models.Flowcell.exists(flowcell_name)
    if flowcell_id:
        LOG.debug("Found flowcell with id %s", flowcell_id)
        return flowcell_id
    LOG.debug("Could not find flowcell")
    return None


def get_demux_id(flowcell_object_id: int) -> Optional[int]:
    """Flowcell object id refers to a database object"""
    demux_id: Optional[int] = models.Demux.exists(flowcell_id=flowcell_object_id, basemask="")
    if demux_id:
        return demux_id
    return None


def get_project_id(project_name: str) -> Optional[int]:
    project_id: Optional[int] = models.Project.exists(project_name=project_name)
    if project_id:
        return project_id
    return None


def get_sample(sample_id: str):
    """Get a unique demux sample."""
    pattern = SAMPLE_PATTERN.format(sample_id)
    return models.Sample.query.filter(
        or_(models.Sample.samplename.like(pattern), models.Sample.samplename == sample_id)
    ).first()


def get_sample_id(sample_id: str, barcode: str) -> Optional[int]:
    sample_id: Optional[int] = models.Sample.exists(sample_name=sample_id, barcode=barcode)
    if sample_id:
        return sample_id
    return None


def get_unaligned_id(sample_id: int, demux_id: int, lane: int) -> Optional[int]:
    unaligned_id: Optional[int] = models.Unaligned.exists(
        sample_id=sample_id, demux_id=demux_id, lane=lane
    )
    if unaligned_id:
        return unaligned_id
    return None


def get_samples(flowcell: str, project_name: Optional[str] = None) -> alchy.Query:
    query: alchy.Query = models.Sample.query.join(
        models.Sample.unaligned, models.Unaligned.demux, models.Demux.flowcell
    )
    if project_name:
        query = query.join(models.Sample.project).filter(models.Project.projectname == project_name)

    query = query.filter(models.Flowcell.flowcellname == flowcell)

    return query


def project_sample_stats(flowcell: str, project_name: Optional[str] = None) -> List[StatsSample]:
    samples_query: alchy.Query = get_samples(flowcell=flowcell, project_name=project_name)
    db_sample: models.Sample
    sample_stats: List[StatsSample] = [
        StatsSample.from_orm(db_sample) for db_sample in samples_query
    ]
    return sample_stats
