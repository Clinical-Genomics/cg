from pathlib import Path
from typing import List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims.samplesheet import (
    LimsFlowcellSample,
    LimsFlowcellSampleBcl2Fastq,
    LimsFlowcellSampleDragen,
)
from cg.models.demultiplex.run_parameters import RunParameters


@pytest.fixture(name="output_dirs_bcl2fastq")
def fixture_output_dirs_bcl2fastq(demultiplexed_runs: Path) -> Path:
    """Return the output path a dir with flow cells that have finished demultiplexing using
    bcl2fastq."""
    return Path(demultiplexed_runs, "bcl2fastq")


@pytest.fixture(name="demux_run_dir_bcl2fastq")
def fixture_demux_run_dir_bcl2fastq(demux_run_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(demux_run_dir, "bcl2fastq")


@pytest.fixture(name="demux_run_dir_dragen")
def fixture_demux_run_dir_dragen(demux_run_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(demux_run_dir, "dragen")


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="novaseq_dir")
def fixture_novaseq_dir(demux_run_dir: Path, flow_cell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demux_run_dir, flow_cell_full_name)


@pytest.fixture(name="flow_cell_dir_bcl2fastq")
def fixture_novaseq_dir_bcl2fastq(demux_run_dir_bcl2fastq: Path, flow_cell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demux_run_dir_bcl2fastq, flow_cell_full_name)


@pytest.fixture(name="flow_cell_dir_dragen")
def fixture_novaseq_dir_dragen(demux_run_dir_dragen: Path, flow_cell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demux_run_dir_dragen, flow_cell_full_name)


@pytest.fixture(name="hiseq_dir")
def fixture_hiseq_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demultiplex_fixtures, "hiseq_run")


@pytest.fixture(name="unknown_run_parameters")
def fixture_unknown_run_parameters(demultiplex_fixtures: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return Path(demultiplex_fixtures, "unknown_run_parameters.xml")


@pytest.fixture(name="run_parameters_missing_flowcell_type")
def fixture_run_parameters_missing_flowcell_type(demultiplex_fixtures: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return Path(demultiplex_fixtures, "runParameters_missing_flowcell_run_field.xml")


@pytest.fixture(name="hiseq_run_parameters")
def fixture_hiseq_run_parameters(hiseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return Path(hiseq_dir, "runParameters.xml")


@pytest.fixture(name="novaseq_run_parameters")
def fixture_novaseq_run_parameters(novaseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return Path(novaseq_dir, "RunParameters.xml")


@pytest.fixture(name="raw_lims_sample")
def fixture_raw_lims_sample(flow_cell_name: str) -> LimsFlowcellSample:
    """Return a raw lims sample"""
    sample = {
        "flowcell_id": flow_cell_name,
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


@pytest.fixture(name="lims_novaseq_samples")
def fixture_lims_novaseq_samples(lims_novaseq_samples_raw: List[dict]) -> List[LimsFlowcellSample]:
    """Return a list of parsed flowcell samples"""
    return [LimsFlowcellSample(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_bcl2fastq_samples")
def fixture_lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[LimsFlowcellSampleBcl2Fastq]:
    """Return a list of parsed flow cell samples"""
    return [LimsFlowcellSampleBcl2Fastq(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_dragen_samples")
def fixture_lims_novaseq_dragen_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[LimsFlowcellSampleDragen]:
    """Return a list of parsed flowcell samples"""
    return [LimsFlowcellSampleDragen(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="novaseq_run_parameters_object")
def fixture_novaseq_run_parameters_object(novaseq_run_parameters: Path) -> RunParameters:
    return RunParameters(novaseq_run_parameters)


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_object")
def fixture_novaseq_bcl2fastq_sample_sheet_object(
    flow_cell_id: str,
    lims_novaseq_bcl2fastq_samples: List[LimsFlowcellSampleBcl2Fastq],
    novaseq_run_parameters_object: RunParameters,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flowcell_id=flow_cell_id,
        lims_samples=lims_novaseq_bcl2fastq_samples,
        run_parameters=novaseq_run_parameters_object,
        bcl_converter="bcl2fastq",
    )


@pytest.fixture(name="novaseq_dragen_sample_sheet_object")
def fixture_novaseq_dragen_sample_sheet_object(
    flow_cell_id: str,
    lims_novaseq_dragen_samples: List[LimsFlowcellSampleDragen],
    novaseq_run_parameters_object: RunParameters,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flowcell_id=flow_cell_id,
        lims_samples=lims_novaseq_dragen_samples,
        run_parameters=novaseq_run_parameters_object,
        bcl_converter="dragen",
    )
