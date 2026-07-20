"""Constants specific for compression."""

import datetime

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX: str = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX: str = "_R2_001.fastq.gz"
FLAG_PATH_SUFFIX: str = ".crunchy.txt"
PENDING_PATH_SUFFIX: str = ".crunchy.pending.txt"

# Read-based memory/time scaling for compression: estimate = slope * reads + intercept
COMPRESSION_MEMORY_PER_READ: float = 8.0330e-08  # GB per read
COMPRESSION_MEMORY_INTERCEPT: float = 5
MEMORY_FLOOR: int = 1
MEMORY_CEIL: int = 500
COMPRESSION_MINUTES_PER_READ: float = 6e-07
COMPRESSION_TIME_INTERCEPT: float = 18.3675
MINUTES_FLOOR: int = 1
MINUTES_CEIL: int = 1440

# Read-based memory/time scaling for decompression - independent, separately tunable from compression
DECOMPRESSION_MEMORY_PER_READ: float = 0
DECOMPRESSION_MEMORY_INTERCEPT: float = 8
DECOMPRESSION_MINUTES_PER_READ: float = 1.0918e-07
DECOMPRESSION_TIME_INTERCEPT: float = 5.51


# Number of days until FASTQs counts as old
FASTQ_DELTA = 21
FASTQ_DATETIME_DELTA = datetime.timedelta(days=FASTQ_DELTA)
