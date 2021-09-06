import logging
from typing import Dict, Iterable, Optional, Union

import sqlalchemy
from cgmodels.demultiplex.sample_sheet import NovaSeqSample, SampleSheet

from cg.apps.cgstats.crud import find
from cg.apps.cgstats.db import models as stats_models
from cg.apps.cgstats.demux_sample import DemuxSample, get_demux_samples, get_dragen_demux_samples
from cg.apps.cgstats.dragen_demux_sample import DragenDemuxSample
from cg.apps.cgstats.stats import StatsAPI
from cg.constants.demultiplexing import DRAGEN_PASSED_FILTER_PCT
from cg.constants.symbols import PERIOD
from cg.models.demultiplex.demux_results import DemuxResults, LogfileParameters

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
    datasource.document_type = demux_results.conversion_stats_path.suffix.strip(PERIOD)
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
    LOG.info("Creating new flowcell object %s", flowcell)
    return flowcell


def create_demux(manager: StatsAPI, flowcell_id: int, datasource_id: int) -> stats_models.Demux:
    demux: stats_models.Demux = manager.Demux()
    demux.flowcell_id = flowcell_id
    demux.datasource_id = datasource_id
    demux.basemask = ""
    demux.time = sqlalchemy.func.now()

    manager.add(demux)
    manager.flush()
    LOG.info("Creating new demux object %s", demux)
    return demux


def create_project(manager: StatsAPI, project_name: str) -> stats_models.Project:
    project: stats_models.Project = manager.Project()
    project.projectname = project_name
    project.time = sqlalchemy.func.now()
    manager.add(project)
    manager.flush()
    LOG.info("Creating new project object %s", project)
    return project


def create_sample(
    manager: StatsAPI, sample_id: str, barcode: str, project_id: int
) -> stats_models.Sample:
    sample: stats_models.Sample = manager.Sample()
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
) -> stats_models.Unaligned:
    unaligned: stats_models.Unaligned = manager.Unaligned()
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
) -> stats_models.Unaligned:
    """Create an unaligned object in cgstats for a sample demultiplexed with Dragen"""
    unaligned: stats_models.Unaligned = manager.Unaligned()
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
        project_id: Optional[int] = find.get_project_id(project_name=project_name)
        if not project_id:
            project_object: stats_models.Project = create_project(
                manager=manager, project_name=project_name
            )
            project_id: int = project_object.project_id
        else:
            LOG.info("Project %s already exists", project_name)
        project_name_to_id[project_name] = project_id
    return project_name_to_id


def _create_samples(
    manager: StatsAPI, sample: NovaSeqSample, project_name_to_id: Dict[str, int]
) -> Union[int, None]:
    """handles sample objects creation for the table `Sample` in cgstats"""

    barcode = sample.index if not sample.second_index else f"{sample.index}+{sample.second_index}"
    sample_id: Optional[int] = find.get_sample_id(sample_id=sample.sample_id, barcode=barcode)
    if sample.project == "indexcheck":
        LOG.debug("Skip adding indexcheck sample to database")
        return
    if not sample_id:
        project_id: int = project_name_to_id[sample.project]
        sample_object: stats_models.Sample = create_sample(
            manager=manager,
            sample_id=sample.sample_id,
            barcode=barcode,
            project_id=project_id,
        )
        sample_id: int = sample_object.sample_id
    return sample_id


def _create_dragen_samples(
    manager: StatsAPI,
    demux_results: DemuxResults,
    project_name_to_id: Dict[str, int],
    demux_id: int,
    sample_sheet: SampleSheet,
):
    """Handles sample creation: creates sample objects and unaligned objects in their respective
    tables in cgstats for samples demultiplexed with Dragen"""

    demux_samples: Dict[int, dict] = get_dragen_demux_samples(
        demux_results=demux_results,
        sample_sheet=sample_sheet,
    )

    sample: NovaSeqSample
    for sample in sample_sheet.samples:
        sample_id: int = _create_samples(
            manager=manager, sample=sample, project_name_to_id=project_name_to_id
        )

        if not sample_id:
            continue

        unaligned_id: Optional[int] = find.get_unaligned_id(
            sample_id=sample_id, demux_id=demux_id, lane=sample.lane
        )
        if not unaligned_id:
            dragen_demux_sample: DragenDemuxSample = demux_samples[sample.lane][sample.sample_id]
            create_dragen_unaligned(
                manager=manager,
                demux_sample=dragen_demux_sample,
                sample_id=sample_id,
                demux_id=demux_id,
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

    demux_samples: Dict[int, Dict[str, DemuxSample]] = get_demux_samples(
        conversion_stats=demux_results.conversion_stats,
        demux_stats_path=demux_results.demux_stats_path,
        sample_sheet=sample_sheet,
    )

    sample: NovaSeqSample
    for sample in sample_sheet.samples:
        sample_id: int = _create_samples(
            manager=manager, sample=sample, project_name_to_id=project_name_to_id
        )

        if not sample_id:
            continue

        unaligned_id: Optional[int] = find.get_unaligned_id(
            sample_id=sample_id, demux_id=demux_id, lane=sample.lane
        )
        if not unaligned_id:
            demux_sample: DemuxSample = demux_samples[sample.lane][sample.sample_id]
            create_unaligned(
                manager=manager,
                demux_sample=demux_sample,
                sample_id=sample_id,
                demux_id=demux_id,
            )


def create_samples(
    manager: StatsAPI,
    demux_results: DemuxResults,
    project_name_to_id: Dict[str, int],
    demux_id: int,
) -> None:
    """dispatches sample object and unaligned object creation for samples based on the
    bcl-converter used in demultiplexing"""
    LOG.info("Creating samples for flowcell %s", demux_results.flowcell.flowcell_full_name)
    sample_sheet: SampleSheet = demux_results.flowcell.get_sample_sheet()

    create_samples_function = {
        "dragen": _create_dragen_samples,
        "bcl2fastq": _create_bcl2fastq_samples,
    }
    create_samples_function[demux_results.bcl_converter](
        manager, demux_results, project_name_to_id, demux_id, sample_sheet
    )


def create_novaseq_flowcell(manager: StatsAPI, demux_results: DemuxResults):
    """Add a novaseq flowcell to CG stats"""
    LOG.info("Adding flowcell information to cgstats")
    support_parameters_id: Optional[int] = find.get_support_parameters_id(
        demux_results=demux_results
    )
    if not support_parameters_id:
        support_parameters: stats_models.Supportparams = create_support_parameters(
            manager=manager, demux_results=demux_results
        )
        support_parameters_id: int = support_parameters.supportparams_id
    else:
        LOG.info("Support parameters already exists")

    datasource_id: Optional[int] = find.get_datasource_id(demux_results=demux_results)
    if not datasource_id:
        datasource_object: stats_models.Datasource = create_datasource(
            manager=manager,
            demux_results=demux_results,
            support_parameters_id=support_parameters_id,
        )
        datasource_id: int = datasource_object.datasource_id
    else:
        LOG.info("Data source already exists")
    flowcell_id: Optional[int] = find.get_flowcell_id(
        flowcell_name=demux_results.flowcell.flowcell_id
    )

    if not flowcell_id:
        flowcell: stats_models.Flowcell = create_flowcell(
            manager=manager, demux_results=demux_results
        )
        flowcell_id: int = flowcell.flowcell_id
    else:
        LOG.info("Flowcell already exists")

    demux_id: Optional[int] = find.get_demux_id(flowcell_object_id=flowcell_id)
    if not demux_id:
        demux_object: stats_models.Demux = create_demux(
            manager=manager, flowcell_id=flowcell_id, datasource_id=datasource_id
        )
        demux_id: int = demux_object.demux_id
    else:
        LOG.info("Demux object already exists")

    project_name_to_id = create_projects(manager=manager, project_names=demux_results.projects)

    create_samples(
        manager=manager,
        demux_results=demux_results,
        project_name_to_id=project_name_to_id,
        demux_id=demux_id,
    )
    manager.commit()
