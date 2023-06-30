import logging
from typing import Dict, Iterable, Optional

import sqlalchemy

from cg.apps.cgstats.db.models import (
    Datasource,
    Demux,
    DemuxSample,
    DragenDemuxSample,
    Flowcell,
    Project,
    Supportparams,
    Sample,
    Unaligned,
)
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
    SampleSheet,
)
from cg.constants.demultiplexing import DRAGEN_PASSED_FILTER_PCT, BclConverter
from cg.constants.symbols import PERIOD
from cg.models.demultiplex.demux_results import DemuxResults, LogfileParameters

LOG = logging.getLogger(__name__)


def create_support_parameters(manager: StatsAPI, demux_results: DemuxResults) -> Supportparams:
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
) -> Datasource:
    datasource = manager.Datasource()
    datasource.runname = demux_results.run_name
    datasource.rundate = demux_results.run_date
    datasource.machine = demux_results.machine_name
    datasource.server = demux_results.demux_host
    datasource.document_path = str(demux_results.conversion_stats_path)
    datasource.document_type = demux_results.conversion_stats_path.suffix.strip(PERIOD)
    datasource.time = sqlalchemy.func.now()
    datasource.supportparams_id = support_parameters_id

    manager.add(datasource)
    manager.flush()
    LOG.info("Creating new datasource object %s", datasource)
    return datasource


def create_flowcell(manager: StatsAPI, demux_results: DemuxResults) -> Flowcell:
    flowcell = manager.Flowcell()
    flowcell.flowcellname = demux_results.flow_cell.id
    flowcell.flowcell_pos = demux_results.flow_cell.position
    flowcell.hiseqtype = "novaseq"
    flowcell.time = sqlalchemy.func.now()

    manager.add(flowcell)
    manager.flush()
    LOG.info("Creating new flowcell object %s", flowcell)
    return flowcell


def create_demux(
    manager: StatsAPI,
    datasource_id: int,
    demux_results: DemuxResults,
    flow_cell_id: int,
) -> Demux:
    demux: Demux = manager.Demux()
    demux.flowcell_id = flow_cell_id
    demux.datasource_id = datasource_id
    if demux_results.bcl_converter == "dragen":
        demux.basemask: str = demux_results.run_info.basemask
    else:
        demux.basemask = ""
    demux.time = sqlalchemy.func.now()

    manager.add(demux)
    manager.flush()
    LOG.info("Creating new demux object %s", demux)
    return demux


def create_project(manager: StatsAPI, project_name: str) -> Project:
    project: Project = manager.Project()
    project.projectname = project_name
    project.time = sqlalchemy.func.now()
    manager.add(project)
    manager.flush()
    LOG.info("Creating new project object %s", project)
    return project


def create_sample(manager: StatsAPI, sample_id: str, barcode: str, project_id: int) -> Sample:
    sample: Sample = manager.Sample()
    sample.project_id = project_id
    sample.samplename = sample_id
    sample.limsid = sample_id.split("_")[0]
    sample.barcode = barcode
    sample.time = sqlalchemy.func.now()

    manager.add(sample)
    manager.flush()
    return sample


def create_unaligned(
    manager: StatsAPI, demux_sample: DemuxSample, sample_id: int, demux_id: int
) -> Unaligned:
    unaligned: Unaligned = manager.Unaligned()
    unaligned.sample_id = sample_id
    unaligned.demux_id = demux_id
    unaligned.lane = demux_sample.lane
    unaligned.yield_mb = round(int(demux_sample.pass_filter_yield) / 1000000, 2)
    unaligned.passed_filter_pct = demux_sample.pass_filter_yield_pc
    unaligned.readcounts = demux_sample.pass_filter_clusters * 2
    unaligned.raw_clusters_per_lane_pct = demux_sample.raw_clusters_pc
    unaligned.perfect_indexreads_pct = (
        round(demux_sample.perfect_barcodes / demux_sample.barcodes * 100, 5)
        if demux_sample.barcodes
        else 0
    )
    unaligned.q30_bases_pct = demux_sample.pass_filter_Q30
    unaligned.mean_quality_score = demux_sample.pass_filter_qscore
    unaligned.time = sqlalchemy.func.now()

    manager.add(unaligned)
    manager.flush()
    return unaligned


def create_dragen_unaligned(
    manager: StatsAPI, demux_sample: DragenDemuxSample, sample_id: int, demux_id: int
) -> Unaligned:
    """Create an unaligned object in cgstats for a sample demultiplexed with Dragen"""
    unaligned: Unaligned = manager.Unaligned()
    unaligned.sample_id: int = sample_id
    unaligned.demux_id: int = demux_id
    unaligned.lane: int = demux_sample.lane
    unaligned.passed_filter_pct: float = DRAGEN_PASSED_FILTER_PCT
    unaligned.readcounts: int = _calculate_read_counts(demux_sample)
    unaligned.perfect_indexreads_pct: float = _calculate_perfect_indexreads_pct(demux_sample)
    unaligned.q30_bases_pct: float = _calculate_q30_bases_pct(demux_sample)
    unaligned.yield_mb: float = _calculate_yield(demux_sample)
    unaligned.mean_quality_score: float = demux_sample.mean_quality_score
    unaligned.time: sqlalchemy.sql.func.now = sqlalchemy.func.now()

    manager.add(unaligned)
    manager.flush()
    return unaligned


def _calculate_perfect_indexreads_pct(demux_sample: DragenDemuxSample) -> float:
    """calculates the percentage of perfect index reads"""
    return (
        round(demux_sample.perfect_reads / demux_sample.reads * 100, 2) if demux_sample.reads else 0
    )


def _calculate_q30_bases_pct(demux_sample: DragenDemuxSample) -> float:
    """calculates the percentage of bases with a sequencing quality score of 30 or over"""
    return (
        round(
            demux_sample.pass_filter_q30
            / (demux_sample.r1_sample_bases + demux_sample.r2_sample_bases)
            * 100,
            2,
        )
        if demux_sample.r1_sample_bases + demux_sample.r2_sample_bases
        else 0
    )


def _calculate_yield(demux_sample: DragenDemuxSample) -> float:
    """calculates the amount of data produced in MB"""
    total_reads = _calculate_read_counts(demux_sample)
    return round(total_reads * demux_sample.read_length / 1000000, 0)


def _calculate_read_counts(demux_sample: DragenDemuxSample) -> int:
    """calculates the number of reads from the number of clusters"""
    return demux_sample.reads * 2


def create_projects(manager: StatsAPI, project_names: Iterable[str]) -> Dict[str, int]:
    project_name_to_id: Dict[str, int] = {}
    for project_name in project_names:
        project: Optional[Project] = get_or_create_project(
            manager=manager, project_name=project_name
        )
        project_name_to_id[project_name] = project.project_id
    return project_name_to_id


def get_or_create_sample(
    manager: StatsAPI, sample: FlowCellSampleNovaSeq6000, project_name_to_id: Dict[str, int]
) -> Sample:
    """Create a new Sample object in the cgstats database if it doesn't already exist."""

    if sample.project == "indexcheck":
        LOG.debug("Skip adding indexcheck sample to database")
        return None

    barcode = f"{sample.index}+{sample.index2}" if sample.index2 else sample.index

    stats_sample: Optional[Sample] = manager.find_handler.get_sample_by_name_and_barcode(
        sample_name=sample.sample_id, barcode=barcode
    )

    if not stats_sample:
        project_id = project_name_to_id[sample.project]

        stats_sample: Sample = create_sample(
            manager=manager,
            sample_id=sample.sample_id,
            barcode=barcode,
            project_id=project_id,
        )

    return stats_sample


def _create_dragen_samples(
    manager: StatsAPI,
    demux_results: DemuxResults,
    project_name_to_id: Dict[str, int],
    demux_id: int,
    sample_sheet: SampleSheet,
):
    """Handles sample creation: creates sample objects and unaligned objects in their respective
    tables in cgstats for samples demultiplexed with Dragen"""

    demux_samples: Dict[int, dict] = manager.find_handler.get_dragen_demux_samples(
        demux_results=demux_results,
        sample_sheet=sample_sheet,
    )

    sample: FlowCellSampleNovaSeq6000Dragen
    for sample in sample_sheet.samples:
        stats_sample: Sample = get_or_create_sample(
            manager=manager, sample=sample, project_name_to_id=project_name_to_id
        )

        if not stats_sample:
            continue

        dragen_demux_sample: DragenDemuxSample = demux_samples[sample.lane][sample.sample_id]

        get_or_create_dragen_unaligned(
            manager=manager,
            dragen_demux_sample=dragen_demux_sample,
            sample_id=stats_sample.sample_id,
            demux_id=demux_id,
            lane=sample.lane,
        )


def _create_bcl2fastq_samples(
    manager: StatsAPI,
    demux_results: DemuxResults,
    project_name_to_id: Dict[str, int],
    demux_id: int,
    sample_sheet: SampleSheet,
):
    """Handles sample creation: creates sample objects and unaligned objects in their respective
    tables in cgstats for samples demultiplexed with bcl2fastq"""

    demux_samples: Dict[int, Dict[str, DemuxSample]] = manager.find_handler.get_demux_samples(
        conversion_stats=demux_results.conversion_stats,
        demux_stats_path=demux_results.demux_stats_path,
        sample_sheet=sample_sheet,
    )

    sample: FlowCellSampleNovaSeq6000Bcl2Fastq
    for sample in sample_sheet.samples:
        stats_sample: Sample = get_or_create_sample(
            manager=manager, sample=sample, project_name_to_id=project_name_to_id
        )

        if not stats_sample:
            continue

        unaligned: Optional[
            Unaligned
        ] = manager.find_handler.get_unaligned_by_sample_id_demux_id_and_lane(
            sample_id=stats_sample.sample_id, demux_id=demux_id, lane=sample.lane
        )
        if not unaligned:
            demux_sample: DemuxSample = demux_samples[sample.lane][sample.sample_id]
            create_unaligned(
                manager=manager,
                demux_sample=demux_sample,
                sample_id=stats_sample.sample_id,
                demux_id=demux_id,
            )


def create_samples(
    manager: StatsAPI,
    demux_results: DemuxResults,
    project_name_to_id: Dict[str, int],
    demux_id: int,
) -> None:
    """dispatches sample object and unaligned object creation for samples based on the
    bcl-converter used in demultiplexing."""
    LOG.info(f"Creating samples for flow cell {demux_results.flow_cell.full_name}")
    sample_sheet: SampleSheet = demux_results.flow_cell.get_sample_sheet()

    create_samples_function = {
        BclConverter.DRAGEN.value: _create_dragen_samples,
        BclConverter.BCL2FASTQ.value: _create_bcl2fastq_samples,
    }
    create_samples_function[demux_results.bcl_converter](
        manager, demux_results, project_name_to_id, demux_id, sample_sheet
    )


def create_novaseq_flowcell(manager: StatsAPI, demux_results: DemuxResults):
    """Add a novaseq flowcell to CG stats"""
    LOG.info("Adding flowcell information to cgstats")

    support_parameters: Supportparams = get_or_create_support_parameters(
        manager=manager, demux_results=demux_results
    )

    datasource: Datasource = get_or_create_datasource(
        manager=manager,
        demux_results=demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )

    flow_cell: Flowcell = get_or_create_flow_cell(manager=manager, demux_results=demux_results)

    demux: Demux = get_or_create_demux(
        manager=manager,
        demux_results=demux_results,
        flow_cell_id=flow_cell.flowcell_id,
        datasource_id=datasource.datasource_id,
    )

    project_name_to_id = create_projects(manager=manager, project_names=demux_results.projects)

    create_samples(
        manager=manager,
        demux_results=demux_results,
        project_name_to_id=project_name_to_id,
        demux_id=demux.demux_id,
    )

    manager.commit()


def get_or_create_dragen_unaligned(
    manager: StatsAPI,
    dragen_demux_sample: DragenDemuxSample,
    sample_id: int,
    demux_id: int,
    lane: int,
) -> Unaligned:
    unaligned = manager.find_handler.get_unaligned_by_sample_id_demux_id_and_lane(
        sample_id=sample_id, demux_id=demux_id, lane=lane
    )

    if not unaligned:
        unaligned = create_dragen_unaligned(
            manager=manager,
            demux_sample=dragen_demux_sample,
            sample_id=sample_id,
            demux_id=demux_id,
        )
    return unaligned


def get_or_create_support_parameters(
    manager: StatsAPI, demux_results: DemuxResults
) -> Supportparams:
    """Create support parameters for demux or retrieve them if they already exist."""
    document_path = str(demux_results.results_dir)

    support_parameters = manager.find_handler.get_support_parameters_by_document_path(
        document_path=document_path
    )

    if not support_parameters:
        support_parameters = create_support_parameters(manager, demux_results)
    else:
        LOG.info("Support parameters already exists")

    return support_parameters


def get_document_stats_path_from_demux(demux_results: DemuxResults) -> str:
    stats_path = {
        BclConverter.BCL2FASTQ.value: demux_results.conversion_stats_path,
        BclConverter.DRAGEN.value: demux_results.demux_stats_path,
    }
    document_path: str = str(stats_path[demux_results.bcl_converter])
    return document_path


def get_or_create_datasource(
    manager: StatsAPI, demux_results: DemuxResults, support_parameters_id: int
) -> Datasource:
    """Create datasource for demux or retrieve it if it already exists."""

    document_path: str = get_document_stats_path_from_demux(demux_results=demux_results)

    datasource: Datasource = manager.find_handler.get_datasource_by_document_path(
        document_path=document_path
    )

    if not datasource:
        datasource = create_datasource(manager, demux_results, support_parameters_id)
    else:
        LOG.info("Data source already exists")

    return datasource


def get_or_create_flow_cell(manager: StatsAPI, demux_results: DemuxResults) -> Flowcell:
    flowcell = manager.find_handler.get_flow_cell_by_name(flow_cell_name=demux_results.flow_cell.id)

    if not flowcell:
        flowcell = create_flowcell(manager, demux_results)
    else:
        LOG.info("Flowcell already exists")

    return flowcell


def get_or_create_demux(
    manager: StatsAPI, demux_results: DemuxResults, flow_cell_id: int, datasource_id: int
) -> Demux:
    demux: Optional[Demux] = manager.find_handler.get_demux_by_flow_cell_id_and_base_mask(
        flowcell_id=flow_cell_id
    )
    if not demux:
        demux = create_demux(
            manager=manager,
            demux_results=demux_results,
            flow_cell_id=flow_cell_id,
            datasource_id=datasource_id,
        )
    else:
        LOG.info("Demux object already exists")

    return demux


def get_or_create_project(manager: StatsAPI, project_name: str) -> Project:
    project: Optional[Project] = manager.find_handler.get_project_by_name(project_name)

    if project:
        LOG.info(f"Project {project_name} already exists")
        return project

    return create_project(manager=manager, project_name=project_name)
