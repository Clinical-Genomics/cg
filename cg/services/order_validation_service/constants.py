from enum import Enum, auto

from cg.constants import PrepCategory, Workflow


class TissueBlockEnum(Enum):
    SMALL: str = auto()
    LARGE: str = auto()
    BLANK: str = ""


ALLOWED_SKIP_RC_BUFFERS = ["Nuclease-free water", "Tris-HCl"]

WORKFLOW_PREP_CATEGORIES: dict[Workflow, list[PrepCategory]] = {
    Workflow.MICROSALT: [PrepCategory.COVID, PrepCategory.MICROBIAL],
    Workflow.TOMTE: [PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING],
}

MINIMUM_VOLUME, MAXIMUM_VOLUME = 20, 130


class ExtractionMethod(Enum):
    EZ1 = "EZ1"
    MAELSTROM = "Maelstrom"
    MAGNAPURE_96 = "MagNaPure 96 (contact Clinical Genomics before submission)"
    QIAGEN_MAGATTRACT = "Qiagen MagAttract"
    QIASYMPHONE = "QIAsymphony"
    OTHER = 'Other (specify in "Comments")'
