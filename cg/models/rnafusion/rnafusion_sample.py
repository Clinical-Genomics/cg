from typing import Dict
from pydantic import BaseModel, ValidationError, validator

from cg.models.analysis import AnalysisModel


class NextflowSample(BaseModel):
    """Nextflow samplesheet model

    Attributes:
        sample: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    sampleID: str
    fastq1: list
    fastq2: list

    @validator('bla')
    def fastq1_fastq2_len_match(fastq1, fastq2):