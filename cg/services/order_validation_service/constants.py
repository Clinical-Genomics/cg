from enum import Enum, StrEnum, auto

from cg.constants import PrepCategory, Workflow


class TissueBlockEnum(StrEnum):
    SMALL: str = auto()
    LARGE: str = auto()
    BLANK: str = ""


class ElutionBuffer(StrEnum):
    OTHER = "Other (add to comment)"
    TRIS_HCL = "Tris-HCl"
    WATER = "Nuclease-free water"


ALLOWED_SKIP_RC_BUFFERS = ["Nuclease-free water", "Tris-HCl"]

WORKFLOW_PREP_CATEGORIES: dict[Workflow, list[PrepCategory]] = {
    Workflow.BALSAMIC: [
        PrepCategory.WHOLE_GENOME_SEQUENCING,
        PrepCategory.WHOLE_EXOME_SEQUENCING,
        PrepCategory.TARGETED_GENOME_SEQUENCING,
    ],
    Workflow.MICROSALT: [PrepCategory.COVID, PrepCategory.MICROBIAL],
    Workflow.TOMTE: [PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING],
    Workflow.MUTANT: [PrepCategory.COVID],
}

MINIMUM_VOLUME, MAXIMUM_VOLUME = 20, 130


class ExtractionMethod(Enum):
    EZ1 = "EZ1"
    MAELSTROM = "Maelstrom"
    MAGNAPURE_96 = "MagNaPure 96 (contact Clinical Genomics before submission)"
    QIAGEN_MAGATTRACT = "Qiagen MagAttract"
    QIASYMPHONE = "QIAsymphony"
    OTHER = 'Other (specify in "Comments")'
