from enum import Enum, auto

from cg.constants import PrepCategory, Workflow


class TissueBlockEnum(Enum):
    SMALL: str = auto()
    LARGE: str = auto()
    BLANK: str = ""


ALLOWED_SKIP_RC_BUFFERS = ["Nuclease-free water", "Tris-HCl"]

WORKFLOW_PREP_CATEGORIES: dict[Workflow, list[PrepCategory]] = {
    Workflow.TOMTE: [PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING],
}
