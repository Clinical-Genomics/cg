import json
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


@pytest.fixture(name="flowcell_name")
def fixture_flowcell_name() -> str:
    return "HVKJCDRXX"


@pytest.fixture(name="flowcell_full_name")
def fixture_flowcell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="demultiplex_fixtures")
def fixture_demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixtures"""
    return apps_dir / "demultiplexing"


@pytest.fixture(name="demultiplexed_runs_dir")
def fixture_demultiplexed_runs_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demultiplex_fixtures / "demultiplexed-runs"


@pytest.fixture(name="output_dirs_bcl2fastq")
def fixture_output_dirs_bcl2fastq(demultiplexed_runs_dir: Path) -> Path:
    """Return the output path a dir with flowcells that have finished demultiplexing using
    bcl2fastq"""
    return demultiplexed_runs_dir / "bcl2fastq"


@pytest.fixture(name="demux_run_dir")
def fixture_demux_run_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demultiplex_fixtures / "flowcell-runs"


@pytest.fixture(name="demux_run_dir_bcl2fastq")
def fixture_demux_run_dir_bcl2fastq(demux_run_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demux_run_dir / "bcl2fastq"


@pytest.fixture(name="demux_run_dir_dragen")
def fixture_demux_run_dir_dragen(demux_run_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demux_run_dir / "dragen"


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="raw_samples_dir")
def fixture_raw_samples_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the raw samples fixtures"""
    return demultiplex_fixtures / "raw_lims_samples"


@pytest.fixture(name="novaseq_dir")
def fixture_novaseq_dir(demux_run_dir: Path, flowcell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return demux_run_dir / flowcell_full_name


@pytest.fixture(name="flowcell_dir_bcl2fastq")
def fixture_novaseq_dir_bcl2fastq(demux_run_dir_bcl2fastq: Path, flowcell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return demux_run_dir_bcl2fastq / flowcell_full_name


@pytest.fixture(name="flowcell_dir_dragen")
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
