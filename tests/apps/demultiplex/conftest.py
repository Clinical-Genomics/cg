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
from cg.apps.demultiplex.sample_sheet.validate import NovaSeqSample
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


@pytest.fixture(name="flow_cell_dir_bcl2fastq")
def fixture_novaseq_dir_bcl2fastq(demux_run_dir_bcl2fastq: Path, flow_cell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demux_run_dir_bcl2fastq, flow_cell_full_name)


@pytest.fixture(name="flow_cell_dir_dragen")
def fixture_novaseq_dir_dragen(demux_run_dir_dragen: Path, flow_cell_full_name: str) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return Path(demux_run_dir_dragen, flow_cell_full_name)


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


# Sample sheet validation


@pytest.fixture(name="sample_sheet_line_sample_1")
def fixture_sample_sheet_line_sample_1() -> str:
    """Return the line in the sample sheet corresponding to a sample."""
    return "HWHMWDMXX,1,ACC7628A68,hg19,ATTCCACACT,TGGTCTTGTT,814206,N,R1,script,814206\n"


@pytest.fixture(name="sample_sheet_line_sample_2")
def fixture_sample_sheet_line_sample_2() -> str:
    """Return the line in the sample sheet corresponding to a sample."""
    return "HWHMWDMXX,1,ACC7628A1,hg19,AGTTAGCTGG,GATGAGAATG,814206,N,R1,script,814206\n"


@pytest.fixture(name="sample_sheet_bcl2fastq_data_header")
def fixture_sample_sheet_bcl2fastq_data_header() -> str:
    """Return the content of a bcl2fastq sample sheet data header without samples."""
    return (
        "[Data]\n"
        "FCID,Lane,SampleID,SampleRef,index,index2,SampleName,Control,Recipe,Operator,Project\n"
    )


@pytest.fixture(name="sample_sheet_dragen_data_header")
def fixture_sample_sheet_dragen_data_header() -> str:
    """Return the content of a dragen sample sheet data_header without samples."""
    return (
        "[Data]\n"
        "FCID,Lane,Sample_ID,SampleRef,index,index2,SampleName,Control,Recipe,Operator,"
        "Sample_Project\n"
    )


@pytest.fixture(name="sample_sheet_samples_no_header")
def fixture_sample_sheet_no_sample_header(
    sample_sheet_line_sample_1: str, sample_sheet_line_sample_2: str
) -> str:
    """Return the content of a sample sheet with samples but without a sample header."""
    return "[Data]\n" + sample_sheet_line_sample_1 + sample_sheet_line_sample_2


@pytest.fixture(name="valid_sample_sheet_bcl2fastq")
def fixture_valid_sample_sheet_bcl2fastq(
    sample_sheet_line_sample_1: str, sample_sheet_line_sample_2: str
) -> str:
    """Return the content of a valid bcl2fastq sample sheet."""
    return (
        "[Data]\n"
        "FCID,Lane,SampleID,SampleRef,index,index2,SampleName,Control,Recipe,Operator,Project\n"
        + sample_sheet_line_sample_1
        + sample_sheet_line_sample_2
    )


@pytest.fixture(name="sample_sheet_bcl2fastq_duplicate_same_lane")
def fixture_sample_sheet_bcl2fastq_duplicate_same_lane(
    valid_sample_sheet_bcl2fastq: str, sample_sheet_line_sample_2: str
):
    """Return the content of a bcl2fastq sample sheet with a duplicated sample in the same lane."""
    return valid_sample_sheet_bcl2fastq + "\n" + sample_sheet_line_sample_2


@pytest.fixture(name="sample_sheet_bcl2fastq_duplicate_different_lane")
def fixture_sample_sheet_bcl2fastq_duplicate_different_lane(valid_sample_sheet_bcl2fastq: str):
    """Return the content of a bcl2fastq sample sheet with a duplicated sample in a different lane."""
    return (
        valid_sample_sheet_bcl2fastq
        + "\n"
        + "HWHMWDMXX,2,ACC7628A1,hg19,AGTTAGCTGG,GATGAGAATG,814206,N,R1,script,814206"
    )


@pytest.fixture(name="valid_sample_sheet_dragen")
def fixture_valid_sample_sheet_dragen(
    sample_sheet_line_sample_1: str, sample_sheet_line_sample_2: str
) -> str:
    """Return the content of a valid dragen sample sheet."""
    return (
        "[Data]\n"
        "FCID,Lane,Sample_ID,SampleRef,index,index2,SampleName,Control,Recipe,Operator,"
        "Sample_Project\n" + sample_sheet_line_sample_1 + sample_sheet_line_sample_2
    )


@pytest.fixture(name="sample_sheet_dragen_duplicate_same_lane")
def fixture_sample_sheet_dragen_duplicate_same_lane(
    valid_sample_sheet_dragen: str, sample_sheet_line_sample_2: str
):
    """Return the content of a dragen sample sheet with a duplicated sample in the same lane."""
    return valid_sample_sheet_dragen + "\n" + sample_sheet_line_sample_2


@pytest.fixture(name="sample_sheet_dragen_duplicate_different_lane")
def fixture_sample_sheet_dragen_duplicate_different_lane(valid_sample_sheet_dragen: str):
    """Return the content of aa dragen sample sheet with a duplicated sample in a different lane."""
    return (
        valid_sample_sheet_dragen
        + "\n"
        + "HWHMWDMXX,2,ACC7628A1,hg19,AGTTAGCTGG,GATGAGAATG,814206,N,R1,script,814206"
    )


@pytest.fixture(name="valid_sample_sheet_bcl2fastq_path")
def fixture_valid_sample_sheet_bcl2fastq_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in bcl2fastq demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Bcl2Fastq.csv")


@pytest.fixture(name="valid_sample_sheet_dragen_path")
def fixture_valid_sample_sheet_dragen_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in dragen demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Dragen.csv")


@pytest.fixture(name="novaseq_sample_1")
def fixture_novaseq_sample_1() -> NovaSeqSample:
    """Return a NovaSeq sample."""
    return NovaSeqSample(
        FCID="HWHMWDMXX",
        Lane=1,
        SampleID="ACC7628A68",
        SampleRef="hg19",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        SampleName="814206",
        Control="N",
        Recipe="R1",
        Operator="script",
        Project="814206",
    )


@pytest.fixture(name="novaseq_sample_2")
def fixture_novaseq_sample_2() -> NovaSeqSample:
    """Return a NovaSeq sample."""
    return NovaSeqSample(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        SampleRef="hg19",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        SampleName="814206",
        Control="N",
        Recipe="R1",
        Operator="script",
        Project="814206",
    )
