"""Import all constants here for easy access"""

from .tags import HK_TAGS, HK_FASTQ_TAGS, MIP_DNA_TAGS, MIP_RNA_TAGS, MICROSALT_TAGS
from .symbols import SPACE, SINGLE_QUOTE, NO_PARENT
from .process import EXIT_FAIL, EXIT_SUCCESS, RETURN_SUCCESS
from .compression import (
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
    FASTQ_DELTA,
    SPRING_SUFFIX,
)
from .sample_sources import METAGENOME_SOURCES, ANALYSIS_SOURCES
from .gene_panel import MASTER_LIST
from .paths import TMP_DIR
from .priority import PRIORITY_MAP, PRIORITY_OPTIONS, REV_PRIORITY_MAP

from .constants import (
    FAMILY_ACTIONS,
    PREP_CATEGORIES,
    SEX_OPTIONS,
    STATUS_OPTIONS,
    CONTAINER_OPTIONS,
    CAPTUREKIT_OPTIONS,
    CAPTUREKIT_CANCER_OPTIONS,
    DEFAULT_CAPTURE_KIT,
    COMBOS,
    COLLABORATORS,
    FLOWCELL_STATUS,
)
