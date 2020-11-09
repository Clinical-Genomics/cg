"""Constants specific for compression"""
import datetime

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX = "_R2_001.fastq.gz"
SPRING_SUFFIX = ".spring"

# Number of days until fastqs counts as old
FASTQ_DELTA = 21
# Get the fastq delta in datetime format
FASTQ_DATETIME_DELTA = datetime.timedelta(days=FASTQ_DELTA)
