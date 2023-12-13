from pydantic import BaseModel

from cg.constants.constants import MicrosaltAppTags


class QualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_control: bool
    application_tag: MicrosaltAppTags
    passes_reads_qc: bool
    passes_mapping_qc: bool
    passes_duplication_qc: bool
    passes_inserts_qc: bool
    passes_coverage_qc: bool
    passes_10x_coverage_qc: bool
