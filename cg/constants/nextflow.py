"""Nextflow related constants."""

from enum import IntEnum
from cg.constants import Workflow

NFX_WORK_DIR = "work"
NFX_SAMPLE_HEADER = "sample"
NFX_READ1_HEADER = "fastq_1"
NFX_READ2_HEADER = "fastq_2"
NFX_SAMPLESHEET_READS_HEADERS = [NFX_READ1_HEADER, NFX_READ2_HEADER]
NFX_SAMPLESHEET_HEADERS = [NFX_SAMPLE_HEADER] + NFX_SAMPLESHEET_READS_HEADERS
DELIVER_FILE_HEADERS = ["format", "id", "path", "path_index", "step", "tag"]
NXF_PID_FILE_ENV = "NXF_PID_FILE"
NXF_JVM_ARGS_ENV = "NXF_JVM_ARGS"
JAVA_MEMORY_HEADJOB = "-Xmx5g"
NEXTFLOW_WORKFLOWS: list = [
    Workflow.RAREDISEASE,
    Workflow.RNAFUSION,
    Workflow.TAXPROFILER,
    Workflow.TOMTE,
]


class SlurmHeadJobDefaults(IntEnum):
    """Default parameters for slurm head jobs."""

    HOURS: int = 96
    MEMORY: int = 10
    NUMBER_TASKS: int = 1
