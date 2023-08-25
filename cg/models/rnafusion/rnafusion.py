from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic.v1 import BaseModel

from cg import resources
from cg.constants.constants import FileFormat, Strandedness
from cg.io.controller import ReadFile
from cg.models.analysis import AnalysisModel
from cg.models.nf_analysis import (
    FileDeliverable,
    NextflowSample,
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
    input: Path
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


class RnafusionSample(NextflowSample):
    """Rnafusion sample sheet model."""

    strandedness: Strandedness


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
        template: List[dict] = cls.get_deliverables_template()
        files: list = []
        for file in template:
            for key, value in file.items():
                if value is None:
                    continue
                file[key] = file[key].replace("CASEID", case_id)
                file[key] = file[key].replace("PATHTOCASE", str(case_path))
            files.append(FileDeliverable(**file))
        return cls(files=files)
