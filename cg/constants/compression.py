"""Constants specific for compression."""

import datetime

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX: str = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX: str = "_R2_001.fastq.gz"
FLAG_PATH_SUFFIX: str = ".crunchy.txt"
MAX_READS_PER_GB: int = 18_000_000
CRUNCHY_MIN_GB_PER_PROCESS: int = 30
PENDING_PATH_SUFFIX: str = ".crunchy.pending.txt"

# Read-based time scaling for compression, in minutes (memory reuses MAX_READS_PER_GB/CRUNCHY_MIN_GB_PER_PROCESS above)
COMPRESSION_MAX_READS_PER_MINUTE: int = 1_700_000
COMPRESSION_MIN_MINUTES_PER_PROCESS: int = 240
COMPRESSION_MAX_MINUTES_PER_PROCESS: int = 2_880

# Read-based memory/time scaling for decompression - independent, separately tunable from compression
DECOMPRESSION_MAX_READS_PER_GB: int = 18_000_000
DECOMPRESSION_MIN_GB_PER_PROCESS: int = 30
DECOMPRESSION_MAX_GB_PER_PROCESS: int = 180
DECOMPRESSION_MAX_READS_PER_MINUTE: int = 850_000
DECOMPRESSION_MIN_MINUTES_PER_PROCESS: int = 120
DECOMPRESSION_MAX_MINUTES_PER_PROCESS: int = 1_440


# Number of days until FASTQs counts as old
FASTQ_DELTA = 21
FASTQ_DATETIME_DELTA = datetime.timedelta(days=FASTQ_DELTA)
