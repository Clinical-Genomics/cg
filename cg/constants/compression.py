"""Constants specific for compression."""

import datetime

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX: str = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX: str = "_R2_001.fastq.gz"
FLAG_PATH_SUFFIX: str = ".crunchy.txt"
MAX_READS_PER_GB: int = 18_000_000
CRUNCHY_MIN_GB_PER_PROCESS: int = 30
PENDING_PATH_SUFFIX: str = ".crunchy.pending.txt"


# Number of days until FASTQs counts as old
FASTQ_DELTA = 21
FASTQ_DATETIME_DELTA = datetime.timedelta(days=FASTQ_DELTA)
