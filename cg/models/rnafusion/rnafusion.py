from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic.v1 import BaseModel, Field

from cg import resources
from cg.constants.constants import FileFormat, Strandedness
from cg.io.controller import ReadFile
from cg.models.analysis import AnalysisModel
from cg.models.nf_analysis import (
    FileDeliverable,
    NextflowSampleSheetEntry,
    PipelineDeliverables,
    PipelineParameters,
)


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: Optional[float]
    after_filtering_q20_rate: Optional[float]
    after_filtering_q30_rate: Optional[float]
    after_filtering_read1_mean_length: Optional[float]
    before_filtering_total_reads: Optional[float]
    bias_5_3: Optional[float]
    pct_adapter: Optional[float]
    pct_mrna_bases: Optional[float]
    pct_ribosomal_bases: Optional[float]
    pct_surviving: Optional[float]
    pct_duplication: Optional[float]
    reads_aligned: Optional[float]
    uniquely_mapped_percent: Optional[float]


class RnafusionParameters(PipelineParameters):
    """Rnafusion parameters."""

    genomes_base: Path
    input: Path = Field(..., alias="sample_sheet_path")
    outdir: Path
    all: bool = False
    arriba: bool = True
    cram: str = "arriba,starfusion"
    fastp_trim: bool = True
    fusioncatcher: bool = True
    fusioninspector_filter: bool = False
    fusionreport_filter: bool = False
    pizzly: bool = False
    squid: bool = False
    starfusion: bool = True
    trim: bool = False
    trim_tail: int = 50


class CommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: Optional[Union[str, Path]]
    resume: Optional[bool]
    profile: Optional[str]
    stub: Optional[bool]
    config: Optional[Union[str, Path]]
    name: Optional[str]
    revision: Optional[str]
    wait: Optional[str]
    id: Optional[str]
    with_tower: Optional[bool]
    use_nextflow: Optional[bool]
    compute_env: Optional[str]
    work_dir: Optional[Union[str, Path]]
    params_file: Optional[Union[str, Path]]


class RnafusionSampleSheetEntry(NextflowSampleSheetEntry):
    """Rnafusion sample sheet model."""

    strandedness: Strandedness

    @staticmethod
    def headers() -> List[str]:
        """Return sample sheet headers."""
        return ["sample", "fastq_1", "fastq_2", "strandedness"]

    def reformat_sample_content(self) -> List[List[str]]:
        """Reformat sample sheet content as a list of list, where each list represents a line in the final file."""
        return [
            [self.name, fastq_forward_read_path, fastq_reverse_read_path, str(self.strandedness)]
            for fastq_forward_read_path, fastq_reverse_read_path in zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            )
        ]


class RnafusionAnalysis(AnalysisModel):
    """Rnafusion analysis model.

    Attributes:
        sample_metrics: retrieved QC metrics associated to a sample
    """

    sample_metrics: Dict[str, RnafusionQCMetrics]


class RnafusionDeliverables(PipelineDeliverables):
    """Specification for pipeline deliverables."""

    @staticmethod
    def get_deliverables_template() -> List[dict]:
        """Return deliverables file template content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=resources.RNAFUSION_BUNDLE_FILENAMES_PATH,
        )

    @classmethod
    def get_deliverables_for_case(cls, case_id: str, case_path: Path):
        """Return RnafusionDeliverables for a given case."""
        deliverable_templates: List[dict] = cls.get_deliverables_template()
        files: list = []
        for file in deliverable_templates:
            for deliverable_field, deliverable_value in file.items():
                if deliverable_value is None:
                    continue
                file[deliverable_field] = file[deliverable_field].replace("CASEID", case_id)
                file[deliverable_field] = file[deliverable_field].replace(
                    "PATHTOCASE", str(case_path)
                )
            files.append(FileDeliverable(**file))
        return cls(files=files)
