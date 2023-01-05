"""Import all constants here for easy access"""

from cg.constants.compression import FASTQ_DELTA, FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.constants.constants import (
    CAPTUREKIT_CANCER_OPTIONS,
    CAPTUREKIT_OPTIONS,
    CASE_ACTIONS,
    COLLABORATORS,
    COMBOS,
    CONTAINER_OPTIONS,
    DEFAULT_CAPTURE_KIT,
    FLOWCELL_Q30_THRESHOLD,
    FLOWCELL_STATUS,
    PREP_CATEGORIES,
    SEX_OPTIONS,
    STATUS_OPTIONS,
    DataDelivery,
    FileExtensions,
    FlowCellStatus,
    Pipeline,
)
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.paths import TMP_DIR
from cg.constants.priority import Priority
from cg.constants.process import EXIT_FAIL, EXIT_SUCCESS, RETURN_SUCCESS
from cg.constants.report import *
from cg.constants.sample_sources import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.constants.symbols import NO_PARENT, SINGLE_QUOTE, SPACE
from cg.constants.housekeeper_tags import HK_FASTQ_TAGS
