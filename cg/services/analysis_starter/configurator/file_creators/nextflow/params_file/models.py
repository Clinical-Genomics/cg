from pathlib import Path

from cg.models.nf_analysis import WorkflowParameters


class RarediseaseParameters(WorkflowParameters):
    """Model for Raredisease parameters."""

    target_bed_file: str
    analysis_type: str
    save_mapped_as_cram: bool
    vcfanno_extra_resources: str
    vep_filters_scout_fmt: str
    sample_id_map: Path


class RNAFusionParameters(WorkflowParameters):
    """RNAFUSION parameters."""


class TaxprofilerParameters(WorkflowParameters):
    """Taxprofiler parameters."""
