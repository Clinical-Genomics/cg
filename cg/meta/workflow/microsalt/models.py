from typing import List, Dict
from pydantic import BaseModel


class BlastPubmlst(BaseModel):
    sequence_type: str
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


class Sample(BaseModel):
    blast_pubmlst: BlastPubmlst
    quast_assembly: QuastAssembly
    blast_resfinder_resistence: List[str]
    picard_markduplicate: PicardMarkduplicate
    microsalt_samtools_stats: MicrosaltSamtoolsStats


class QualityMetrics(BaseModel):
    samples: Dict[str, Sample]
