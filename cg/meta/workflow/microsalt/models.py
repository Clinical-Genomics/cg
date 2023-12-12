from typing import List, Dict
from pydantic import BaseModel
from cg.constants.constants import MicrosaltAppTags

from cg.store.models import Sample


class BlastPubmlst(BaseModel):
    sequence_type: MicrosaltAppTags
    thresholds: str


class QuastAssembly(BaseModel):
    estimated_genome_length: int
    gc_percentage: str
    n50: int
    necessary_contigs: int


class PicardMarkduplicate(BaseModel):
    insert_size: int
    duplication_rate: float


class MicrosaltSamtoolsStats(BaseModel):
    total_reads: int
    mapped_rate: float
    average_coverage: float
    coverage_10x: float
    coverage_30x: float
    coverage_50x: float
    coverage_100x: float


class SampleMetrics(BaseModel):
    blast_pubmlst: BlastPubmlst
    quast_assembly: QuastAssembly
    blast_resfinder_resistence: List[str]
    picard_markduplicate: PicardMarkduplicate
    microsalt_samtools_stats: MicrosaltSamtoolsStats


class QualityMetrics(BaseModel):
    samples: Dict[str, SampleMetrics]


class QualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_negative_control: bool
    application_tag: MicrosaltAppTags
