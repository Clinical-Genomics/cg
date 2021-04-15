import logging
from typing import Optional

from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults

LOG = logging.getLogger(__name__)


def get_support_parameters_id(manager: StatsAPI, demux_results: DemuxResults) -> Optional[int]:
    """Fetch the id of the support parameters if post exists"""
    LOG.debug("Search for support parameters with file %s", demux_results.results_dir)
    support_parameters_id: Optional[int] = manager.Supportparams.exists(
        str(demux_results.results_dir)
    )
    if support_parameters_id:
        LOG.debug("Found support parameters with id %s", support_parameters_id)
        return support_parameters_id
    LOG.debug("Could not find support parameters")
    return None


def get_datasource_id(manager: StatsAPI, demux_results: DemuxResults) -> Optional[int]:
    """Fetch the datasource id for a certain run"""
    LOG.debug("Search for datasource with file %s", demux_results.conversion_stats_path)
    datasource_id: Optional[int] = manager.Datasource.exists(
        str(demux_results.conversion_stats_path)
    )
    if datasource_id:
        LOG.debug("Found datasource with id %s", datasource_id)
        return datasource_id
    LOG.debug("Could not find datasource")
    return None


def get_flowcell_id(manager: StatsAPI, flowcell_name: str) -> Optional[int]:
    LOG.debug("Search for flowcell %s", flowcell_name)
    flowcell_id: Optional[int] = manager.Flowcell.exists(flowcell_name)
    if flowcell_id:
        LOG.debug("Found flowcell with id %s", flowcell_id)
        return flowcell_id
    LOG.debug("Could not find flowcell")
    return None


def get_demux_id(manager: StatsAPI, flowcell_id: int) -> Optional[int]:
    demux_id: Optional[int] = manager.Demux.exists(flowcell_id=flowcell_id, basemask="")
    if demux_id:
        return demux_id
    return None
