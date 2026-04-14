"""Import all constants here for easy access"""

from cg.constants.compression import FASTQ_DELTA as FASTQ_DELTA
from cg.constants.compression import FASTQ_FIRST_READ_SUFFIX as FASTQ_FIRST_READ_SUFFIX
from cg.constants.compression import FASTQ_SECOND_READ_SUFFIX as FASTQ_SECOND_READ_SUFFIX
from cg.constants.constants import CAPTUREKIT_CANCER_OPTIONS as CAPTUREKIT_CANCER_OPTIONS
from cg.constants.constants import CAPTUREKIT_OPTIONS as CAPTUREKIT_OPTIONS
from cg.constants.constants import CONTAINER_OPTIONS as CONTAINER_OPTIONS
from cg.constants.constants import DEFAULT_CAPTURE_KIT as DEFAULT_CAPTURE_KIT
from cg.constants.constants import (
    DNA_WORKFLOWS_WITH_SCOUT_38_UPLOAD as DNA_WORKFLOWS_WITH_SCOUT_38_UPLOAD,
)
from cg.constants.constants import STATUS_OPTIONS as STATUS_OPTIONS
from cg.constants.constants import DataDelivery as DataDelivery
from cg.constants.constants import FileExtensions as FileExtensions
from cg.constants.constants import SequencingRunDataAvailability as SequencingRunDataAvailability
from cg.constants.constants import SexOptions as SexOptions
from cg.constants.gene_panel import GenePanelMasterList as GenePanelMasterList
from cg.constants.housekeeper_tags import HK_FASTQ_TAGS as HK_FASTQ_TAGS
from cg.constants.housekeeper_tags import HK_MULTIQC_HTML_TAG as HK_MULTIQC_HTML_TAG
from cg.constants.housekeeper_tags import SequencingFileTag as SequencingFileTag
from cg.constants.paths import TMP_DIR as TMP_DIR
from cg.constants.priority import Priority as Priority
from cg.constants.process import EXIT_FAIL as EXIT_FAIL
from cg.constants.process import EXIT_SUCCESS as EXIT_SUCCESS
from cg.constants.report import *  # noqa
from cg.constants.sample_sources import ANALYSIS_SOURCES as ANALYSIS_SOURCES
from cg.constants.sample_sources import METAGENOME_SOURCES as METAGENOME_SOURCES
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD as FLOWCELL_Q30_THRESHOLD
from cg.constants.symbols import SPACE as SPACE
