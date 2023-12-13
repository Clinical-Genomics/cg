from pydantic import BaseModel

from cg.constants.constants import MicrosaltAppTags


class QualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_negative_control: bool
    application_tag: MicrosaltAppTags
