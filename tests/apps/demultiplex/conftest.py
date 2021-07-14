import json
from pathlib import Path
from typing import Dict, List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims.samplesheet import (
    LimsFlowcellSample,
    LimsFlowcellSampleBcl2Fastq,
    LimsFlowcellSampleDragen,
)
from cg.models.demultiplex.run_parameters import RunParameters


@pytest.fixture(name="demultiplex_fixtures")
def fixture_demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixtures"""
    return apps_dir / "demultiplexing"


@pytest.fixture(name="demux_run_dir")
def fixture_demux_run_dir(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "flowcell_runs"


@pytest.fixture(name="demultiplexed_runs_dir")
def fixture_demultiplexed_runs_dir(demultiplex_fixtures: Path) -> Path:
    """returns the path to all finished demux fixtures"""
    return demultiplex_fixtures / "demultiplexed_runs"


@pytest.fixture(name="flowcell_name")
def fixture_flowcell_name() -> str:
    return "HVKJCDRXX"


@pytest.fixture(name="flowcell_full_name")
def fixture_flowcell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="novaseq_dir")
def fixture_novaseq_dir(demux_run_dir: Path, flowcell_full_name: str) -> Path:
    return demux_run_dir / flowcell_full_name


# fixtures related to bcl2fastq demultiplexing of novaseq flowcells
# 1. run directories (pre demultiplexing)
@pytest.fixture(name="bcl2fastq_demux_run_dir")
def fixture_bcl2fastq_demux_run_dir(demux_run_dir: Path) -> Path:
    return demux_run_dir / "bcl2fastq"


@pytest.fixture(name="bcl2fastq_flowcell_name")
def fixture_bcl2fastq_flowcell_name() -> str:
    return "HNC2FDSXY"


@pytest.fixture(name="bcl2fastq_flowcell_full_name")
def fixture_bcl2fastq_flowcell_full_name() -> str:
    return "210428_A00689_0260_BHNC2FDSXY"


@pytest.fixture(name="bcl2fastq_flowcell_dir")
def fixture_bcl2fastq_flowcell_dir(
    bcl2fastq_demux_run_dir: Path, bcl2fastq_flowcell_full_name: str
) -> Path:
    return bcl2fastq_demux_run_dir / bcl2fastq_flowcell_full_name


# 2. output directories (post demultiplexing)


@pytest.fixture(name="bcl2fastq_output_dirs")
def fixture_bcl2fastq_output_dirs(finished_demuxes_dir: Path) -> Path:
    return finished_demuxes_dir / "bcl2fastq"


@pytest.fixture(name="bcl2fastq_demux_outdir")
def fixture_bcl2fastq_demux_outdir(
    bcl2fastq_output_dirs: Path, bcl2fastq_flowcell_full_name: Path
) -> Path:
    """return the path to a finished demultiplexed run (bcl2fastq)"""
    return bcl2fastq_output_dirs / bcl2fastq_flowcell_full_name


@pytest.fixture(name="bcl2fastq_unaligned_dir")
def fixture_bcl2fastq_unaligned_dir(bcl2fastq_demux_outdir: Path) -> Path:
    """return the path to a bcl2fastq unaligned dir"""
    return bcl2fastq_demux_outdir / "Unaligned"


@pytest.fixture(name="bcl2fastq_stats_dir")
def fixture_bcl2fastq_stats_dir(bcl2fastq_unaligned_dir: Path) -> Path:
    """return the path to a bcl2fastq Stats dir"""
    return bcl2fastq_unaligned_dir / "Stats"


@pytest.fixture(name="bcl2fastq_conversion_stats")
def fixture_bcl2fastq_conversion_stats(bcl2fastq_stats_dir: Path) -> Path:
    """return the path to the conversion stats file"""
    return bcl2fastq_stats_dir / "ConversionStats.xml"


@pytest.fixture(name="bcl2fastq_demultiplexing_stats")
def fixture_bcl2fastq_demultiplexing_stats(bcl2fastq_stats_dir: Path) -> Path:
    """return the path to the demultiplexing stats file"""
    return bcl2fastq_stats_dir / "DemultiplexingStats.xml"


@pytest.fixture(name="bcl2fastq_demux_stats_files")
def fixture_bcl2fastq_demux_stats_files(
    bcl2fastq_conversion_stats: Path, bcl2fastq_demultiplexing_stats: Path
) -> Dict:
    """return a fixture for bcl2fastq demux_stats_files"""
    return {
        "conversion_stats": bcl2fastq_conversion_stats,
        "demultiplexing_stats": bcl2fastq_demultiplexing_stats,
        "runinfo": "",
    }


# fixtures related to dragen demultiplexing of novaseq flowcells
# 1. run directories (bcl files)
@pytest.fixture(name="dragen_demux_run_dir")
def fixture_dragen_demux_run_dir_dragen(demux_run_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demux_run_dir / "dragen"


@pytest.fixture(name="dragen_flowcell_name")
def fixture_dragen_flowcell_name() -> str:
    return "HNC2FDSXY"


@pytest.fixture(name="dragen_flowcell_full_name")
def fixture_dragen_flowcell_full_name() -> str:
    return "210428_A00689_0260_BHNC2FDSXY"


@pytest.fixture(name="dragen_flowcell_dir")
def fixture_dragen_novaseq_dir(dragen_demux_run_dir: Path, dragen_flowcell_full_name: str) -> Path:
    return dragen_demux_run_dir / dragen_flowcell_full_name


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="raw_samples_dir")
def fixture_raw_samples_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the raw samples fixtures"""
    return demultiplex_fixtures / "raw_lims_samples"


@pytest.fixture(name="novaseq_dir_dragen")
def fixture_novaseq_dir_dragen(demux_run_dir_dragen: Path, flowcell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return demux_run_dir_dragen / flowcell_full_name


@pytest.fixture(name="hiseq_dir")
def fixture_hiseq_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return demultiplex_fixtures / "hiseq_run"


@pytest.fixture(name="unknown_run_parameters")
def fixture_unknown_run_parameters(demultiplex_fixtures: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return demultiplex_fixtures / "unknown_run_parameters.xml"


@pytest.fixture(name="run_parameters_missing_flowcell_type")
def fixture_run_parameters_missing_flowcell_type(demultiplex_fixtures: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return demultiplex_fixtures / "runParameters_missing_flowcell_run_field.xml"


@pytest.fixture(name="hiseq_run_parameters")
def fixture_hiseq_run_parameters(hiseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return hiseq_dir / "runParameters.xml"


@pytest.fixture(name="novaseq_run_parameters")
def fixture_novaseq_run_parameters(novaseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return novaseq_dir / "RunParameters.xml"


@pytest.fixture(name="raw_lims_sample")
def fixture_raw_lims_sample(flowcell_name: str) -> LimsFlowcellSample:
    """Return a raw lims sample"""
    sample = {
        "flowcell_id": flowcell_name,
        "lane": 1,
        "sample_id": "ACC7628A20",
        "sample_ref": "hg19",
        "index": "ACTGGTGTCG-ACAGGACTTG",
        "description": "",
        "sample_name": "814206",
        "control": "N",
        "recipe": "R1",
        "operator": "script",
        "project": "814206",
    }
    return LimsFlowcellSample(**sample)


@pytest.fixture(name="lims_novaseq_samples_file")
def fixture_lims_novaseq_samples_file(raw_samples_dir: Path) -> Path:
    """Return the path to a file with sample info in lims format"""
    return raw_samples_dir / "raw_samplesheet_novaseq.json"


@pytest.fixture(name="lims_novaseq_samples")
def fixture_lims_novaseq_samples(lims_novaseq_samples_file: Path) -> List[LimsFlowcellSample]:
    """Return a list of parsed flowcell samples"""
    with open(lims_novaseq_samples_file, "r") as in_file:
        raw_samples: List[dict] = json.load(in_file)
        return [LimsFlowcellSample(**sample) for sample in raw_samples]


@pytest.fixture(name="lims_novaseq_bcl2fastq_samples")
def fixture_lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_file: Path,
) -> List[LimsFlowcellSampleBcl2Fastq]:
    """Return a list of parsed flowcell samples"""
    with open(lims_novaseq_samples_file, "r") as in_file:
        raw_samples: List[dict] = json.load(in_file)
        return [LimsFlowcellSampleBcl2Fastq(**sample) for sample in raw_samples]


@pytest.fixture(name="lims_novaseq_dragen_samples")
def fixture_lims_novaseq_dragen_samples(
    lims_novaseq_samples_file: Path,
) -> List[LimsFlowcellSampleDragen]:
    """Return a list of parsed flowcell samples"""
    with open(lims_novaseq_samples_file, "r") as in_file:
        raw_samples: List[dict] = json.load(in_file)
        return [LimsFlowcellSampleDragen(**sample) for sample in raw_samples]


@pytest.fixture(name="novaseq_run_parameters_object")
def fixture_novaseq_run_parameters_object(novaseq_run_parameters: Path) -> RunParameters:
    return RunParameters(novaseq_run_parameters)


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_object")
def fixture_novaseq_bcl2fastq_sample_sheet_object(
    flowcell_name: str,
    lims_novaseq_bcl2fastq_samples: List[LimsFlowcellSampleBcl2Fastq],
    novaseq_run_parameters_object: RunParameters,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flowcell_id=flowcell_name,
        lims_samples=lims_novaseq_bcl2fastq_samples,
        run_parameters=novaseq_run_parameters_object,
        bcl_converter="bcl2fastq",
    )


@pytest.fixture(name="novaseq_dragen_sample_sheet_object")
def fixture_novaseq_dragen_sample_sheet_object(
    flowcell_name: str,
    lims_novaseq_dragen_samples: List[LimsFlowcellSampleDragen],
    novaseq_run_parameters_object: RunParameters,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flowcell_id=flowcell_name,
        lims_samples=lims_novaseq_dragen_samples,
        run_parameters=novaseq_run_parameters_object,
        bcl_converter="dragen",
    )


# @pytest.fixture(name="finished_dragen_demux_dir")
# def fixture_finish_bcl2fastq_demux_dir(finished_demuxes_dir: Path) -> Path:
#     """returns the path to all finished bcl2fastq demux fixtures"""
#     return finished_demuxes_dir / "dragen"
#
#
#
#
# @pytest.fixture(name="dragen_demux_outdir")
# def fixture_dragen_demux_outdir(finished_dragen_demux_dir: Path) -> Path:
#     """return the path to a finished demultiplexed run (dragen)"""
#     return finished_dragen_demux_dir / "210428_A00689_0260_BHNC2FDSXY"
#
#
#
# @pytest.fixture(name="dragen_unaligned_dir")
# def fixture_dragen_unaligned_dir(finished_dragen_demux_dir: Path) -> Path:
#     """return the path to a bcl2fastq unaligned dir"""
#     return finished_dragen_demux_dir / "Unaligned"
#
#
#
# @pytest.fixture(name="dragen_reports_dir")
# def fixture_dragen_reports_dir(dragen_unaligned_dir: Path) -> Path:
#     """return the path to a Dragen Reports dir"""
#     return dragen_unaligned_dir / "Reports"
#
#
#
#
# @pytest.fixture(name="dragen_adapter_metrics")
# def fixture_dragen_adapter_metrics(dragen_reports_dir: Path) -> Path:
#     """return the path to the adapter metrics file"""
#     return dragen_reports_dir / "Adapter_Metrics.csv"
#
#
# @pytest.fixture(name="dragen_demultiplex_stats")
# def fixture_dragen_demultiplex_stats(dragen_reports_dir: Path) -> Path:
#     """return the path to the demultiplex stats file"""
#     return dragen_reports_dir / "Demultiplex_Stats.csv"
#
#
# @pytest.fixture(name="dragen_run_info")
# def fixture_dragen_run_info(dragen_reports_dir: Path) -> Path:
#     """return the path to the run info file"""
#     return dragen_reports_dir / "RunInfo.xml"
#
#
#
#
# @pytest.fixture(name="dragen_demux_stats_files")
# def fixture_dragen_demux_stats_files(
#     dragen_adapter_metrics: Path, dragen_demultiplex_stats: Path, dragen_run_info: Path
# ) -> Dict:
#     """return a fixture for dragen demux_stats_files"""
#     return {
#         "conversion_stats": dragen_adapter_metrics,
#         "demultiplexing_stats": dragen_demultiplex_stats,
#         "runinfo": dragen_run_info,
#     }
