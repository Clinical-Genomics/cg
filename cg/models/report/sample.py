from datetime import datetime
from typing import Optional, List

from cg.constants.constants import ANALYSIS_TYPES

from cg.constants.orderforms import SOURCE_TYPES, CASE_PROJECT_TYPES
from cg.constants import STATUS_OPTIONS
from cg.constants.gender import Gender
from pydantic import BaseModel


class ApplicationModel(BaseModel):
    """
    Analysis application attributes model

    Attributes:
        tag: application identifier
        version: application version
        description: analysis description
        limitations: application limitations
    """

    tag: str
    version: int
    description: str
    limitations: str


class DataAnalysisModel(BaseModel):
    """
    Model that describes the pipeline used for the data analysis

    Attributes:
        pipeline: data analysis pipeline
        pipeline_version: pipeline version
        gender: gender estimated by the pipeline
        capture_kit: panel bed used for the analysis
        capture_kit_version: panel bed version
        type: analysis type carried out; BALSAMIC specific
    """

    pipeline: CASE_PROJECT_TYPES
    pipeline_version: str
    gender: Gender
    capture_kit: Optional[str] = None
    capture_kit_version: Optional[str] = None
    type: Optional[ANALYSIS_TYPES] = None


class MetricsModel(BaseModel):
    """
    Metrics model associated to a specific sample

    Attributes:
        million_read_pairs: number of million read pairs obtained
        mapped_reads: percentage of reads aligned to the reference sequence; MIP specific
        target_coverage: mean coverage of a target region; MIP specific
        target_bases_10X: percent of targeted bases that are covered to 10X coverage or more; MIP specific
        target_bases_250X: percent of targeted bases that are covered to 250X coverage or more; BALSAMIC specific
        target_bases_500X: percent of targeted bases that are covered to 500X coverage or more; BALSAMIC specific
        duplicates: fraction of mapped sequence that is marked as duplicate
        median_coverage: median coverage in bases
        mean_insert_size: mean insert size of the distribution; BALSAMIC specific
        fold_80: fold 80 base penalty; BALSAMIC specific
    """

    million_read_pairs: float
    mapped_reads: Optional[float] = None
    target_coverage: Optional[float] = None
    target_bases_10X: Optional[float] = None
    target_bases_250X: Optional[float] = None
    target_bases_500X: Optional[float] = None
    duplicates: float
    median_coverage: Optional[float] = None
    mean_insert_size: Optional[float] = None
    fold_80: Optional[float] = None


class MethodsModel(BaseModel):
    """
    Model describing the methods used for preparation and sequencing of the samples

    Attributes:
        library_prep: library preparation method
        sequencing: sequencing procedure
    """

    library_prep: str
    sequencing: str


class TimestampModel(BaseModel):
    """
    Model describing the processing timestamp of a specific sample

    Atributes:
        ordered_at: order date
        received_at: arrival date
        prepared_at: library preparation date
        sequenced_at: sequencing date
        delivered_at: delivery date
        processing_days: days between sample arrival and delivery
    """

    ordered_at: datetime
    received_at: datetime
    prepared_at: datetime
    sequenced_at: datetime
    delivered_at: datetime
    processing_days: int


class SampleModel(BaseModel):
    """
    Sample attributes model

    Attributes:
        name: sample name
        id: sample internal ID
        ticket: ticket number
        gender: sample gender provided by the customer
        source: sample type/source
        tumor: wheter the sample is a tumor or normal one; BALSAMIC specific
        application: analysis application
        data_analysis: pipeline attributes
        metrics: sample metrics of interest
        status: sample status provided by the customer; MIP specific
        panels: list of sample specific panels; MIP specific
        timestamp: processing timestamp attributes
    """

    name: str
    id: str
    ticket: int
    gender: Gender
    source: SOURCE_TYPES
    tumor: Optional[bool] = None
    application: ApplicationModel
    methods: MethodsModel
    data_analysis: DataAnalysisModel
    metrics: MetricsModel
    status: Optional[STATUS_OPTIONS] = None
    panels: Optional[List[str]] = None
    timestamp: TimestampModel
