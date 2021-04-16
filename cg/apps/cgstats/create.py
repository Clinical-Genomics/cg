import logging
from typing import Optional

import sqlalchemy
from cg.apps.cgstats import find
from cg.models.demultiplex.demux_results import DemuxResults, LogfileParameters

from cgstats.db import models as stats_models

from .stats import StatsAPI

LOG = logging.getLogger(__name__)


def create_support_parameters(
    manager: StatsAPI, demux_results: DemuxResults
) -> stats_models.Supportparams:
    logfile_parameters: LogfileParameters = demux_results.get_logfile_parameters()
    support_parameters = manager.Supportparams()
    support_parameters.document_path = str(
        demux_results.results_dir
    )  # This is the unaligned directory
    support_parameters.idstring = logfile_parameters.id_string
    support_parameters.program = logfile_parameters.program
    support_parameters.commandline = logfile_parameters.command_line
    support_parameters.sampleconfig_path = str(demux_results.sample_sheet_path)
    support_parameters.sampleconfig = demux_results.sample_sheet_path.read_text()
    support_parameters.time = logfile_parameters.time
    manager.add(support_parameters)
    manager.flush()
    LOG.info("Creating new support parameters object %s", support_parameters)
    return support_parameters


def create_datasource(
    manager: StatsAPI, demux_results: DemuxResults, support_parameters_id: int
) -> stats_models.Datasource:
    datasource = manager.Datasource()
    datasource.runname = demux_results.run_name
    datasource.rundate = demux_results.run_date
    datasource.machine = demux_results.machine_name
    datasource.server = demux_results.demux_host
    datasource.document_path = str(demux_results.conversion_stats_path)
    datasource.document_type = "xml"
    datasource.time = sqlalchemy.func.now()
    datasource.supportparams_id = support_parameters_id

    manager.add(datasource)
    manager.flush()
    LOG.info("Creating new datasource object %s", datasource)
    return datasource


def create_flowcell(manager: StatsAPI, demux_results: DemuxResults) -> stats_models.Flowcell:
    flowcell = manager.Flowcell()
    flowcell.flowcellname = demux_results.flowcell.flowcell_id
    flowcell.flowcell_pos = demux_results.flowcell.flowcell_position
    flowcell.hiseqtype = "novaseq"
    flowcell.time = sqlalchemy.func.now()

    manager.add(flowcell)
    manager.flush()
    return flowcell


def create_demux(manager: StatsAPI, flowcell_id: int, datasource_id: int):
    demux: stats_models.Demux = manager.Demux()
    demux.flowcell_id = flowcell_id
    demux.datasource_id = datasource_id
    demux.basemask = ""
    demux.time = sqlalchemy.func.now()

    manager.add(demux)
    manager.flush()
    return demux


def create_novaseq_flowcell(manager: StatsAPI, demux_results: DemuxResults):
    """Add a novaseq flowcell to CG stats"""
    support_parameters_id: Optional[int] = find.get_support_parameters_id(
        manager=manager, demux_results=demux_results
    )
    if not support_parameters_id:
        support_parameters: stats_models.Supportparams = create_support_parameters(
            manager=manager, demux_results=demux_results
        )
        support_parameters_id: int = support_parameters.supportparams_id
    datasource_id: Optional[int] = find.get_datasource_id(
        manager=manager, demux_results=demux_results
    )
    if not datasource_id:
        datasource_object: stats_models.Datasource = create_datasource(
            manager=manager, demux_results=demux_results, datasource_id=datasource_id
        )
        datasource_id: int = datasource_object.datasource_id
    flowcell_id: Optional[int] = find.get_flowcell_id(
        manager=manager, flowcell_name=demux_results.flowcell.flowcell_id
    )
    if not flowcell_id:
        flowcell: stats_models.Flowcell = create_flowcell(
            manager=manager, demux_results=demux_results
        )
        flowcell_id: int = flowcell.flowcell_id
    demux_id: Optional[int] = find.get_demux_id(manager=manager, flowcell_object_id=flowcell_id)
    if not demux_id:
        demux_object: stats_models.Demux = create_demux(
            manager=manager, flowcell_id=flowcell_id, datasource_id=datasource_id
        )
        demux_id: int = demux_object.demux_id
