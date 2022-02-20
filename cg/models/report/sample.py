from datetime import datetime
from typing import Optional, Union

from cg.constants.gender import Gender
from pydantic import BaseModel, validator
from cg.models.report.validators import (
    validate_empty_field,
    validate_boolean,
    validate_rml_sample,
    validate_float,
    validate_date,
)


class ApplicationModel(BaseModel):
    """
    Analysis application attributes model

    Attributes:
        tag: application identifier; source: StatusDB/application/tag
        version: application version; source: LIMS/sample/application_version
        prep_category: library preparation category; source: StatusDB/application/prep_category
        description: analysis description; source: StatusDB/application/description
        limitations: application limitations; source: StatusDB/application/limitations
        accredited: if the sample associated process is accredited or not; ; source: StatusDB/application/is_accredited

    """

    tag: str
    version: Union[int, str] = None
    prep_category: Optional[str]
    description: Optional[str]
    limitations: Optional[str]
    accredited: bool

    _prep_category = validator("prep_category", always=True, allow_reuse=True)(validate_rml_sample)
    _values = validator(
        "tag",
        "version",
        "prep_category",
        "description",
        "limitations",
        always=True,
        allow_reuse=True,
    )(validate_empty_field)


class MethodsModel(BaseModel):
    """
    Model describing the methods used for preparation and sequencing of the samples

    Attributes:
        library_prep: library preparation method; source: LIMS/sample/prep_method
        sequencing: sequencing procedure; source: LIMS/sample/sequencing_method
    """

    library_prep: Optional[str]
    sequencing: Optional[str]

    _values = validator("library_prep", "sequencing", always=True, allow_reuse=True)(
        validate_empty_field
    )


class TimestampModel(BaseModel):
    """
    Model describing the processing timestamp of a specific sample

    Atributes:
        ordered_at: order date; source: StatusDB/sample/ordered_at
        received_at: arrival date; source: StatusDB/sample/received_at
        prepared_at: library preparation date; source: StatusDB/sample/prepared_at
        sequenced_at: sequencing date; source: StatusDB/sample/sequenced_at
        delivered_at: delivery date; source: StatusDB/sample/delivered_at
        processing_days: days between sample arrival and delivery; source: CG workflow
    """

    ordered_at: Union[datetime, str] = None
    received_at: Union[datetime, str] = None
    prepared_at: Union[datetime, str] = None
    sequenced_at: Union[datetime, str] = None
    delivered_at: Union[datetime, str] = None
    processing_days: Union[int, str] = None

    _values = validator(
        "ordered_at",
        "received_at",
        "prepared_at",
        "sequenced_at",
        "delivered_at",
        always=True,
        allow_reuse=True,
    )(validate_date)
    _processing_days = validator("processing_days", always=True, allow_reuse=True)(
        validate_empty_field
    )


class MetadataModel(BaseModel):
    """
    Metrics and trending data model associated to a specific sample

    Attributes:
        genome_build: build version of the genome reference
        capture_kit: panel bed used for the analysis
        capture_kit_version: panel bed version; BALSAMIC specific
        analysis_type: analysis type carried out; BALSAMIC specific
        gender: gender estimated by the pipeline
        million_read_pairs: number of million read pairs obtained
        mapped_reads: percentage of reads aligned to the reference sequence; MIP specific
        duplicates: fraction of mapped sequence that is marked as duplicate
        target_coverage: mean coverage of a target region; MIP specific
        target_bases_10X: percent of targeted bases that are covered to 10X coverage or more; MIP specific
        target_bases_250X: percent of targeted bases that are covered to 250X coverage or more; BALSAMIC specific
        target_bases_500X: percent of targeted bases that are covered to 500X coverage or more; BALSAMIC specific
        median_coverage: median coverage in bases
        mean_insert_size: mean insert size of the distribution; BALSAMIC specific
        fold_80: fold 80 base penalty; BALSAMIC specific
    """

    genome_build: Optional[str]
    capture_kit: Optional[str]
    capture_kit_version: Optional[str]
    analysis_type: Optional[str]
    gender: Optional[str] = Gender.UNKNOWN
    million_read_pairs: Union[float, str] = None
    mapped_reads: Union[float, str] = None
    duplicates: Union[float, str] = None
    target_coverage: Union[float, str] = None
    target_bases_10X: Union[float, str] = None
    target_bases_250X: Union[float, str] = None
    target_bases_500X: Union[float, str] = None
    median_coverage: Union[float, str] = None
    mean_insert_size: Union[float, str] = None
    fold_80: Union[float, str] = None

    _str_values = validator(
        "genome_build",
        "capture_kit",
        "capture_kit_version",
        "analysis_type",
        "gender",
        always=True,
        allow_reuse=True,
    )(validate_empty_field)

    _float_values = validator(
        "million_read_pairs",
        "mapped_reads",
        "duplicates",
        "target_coverage",
        "target_bases_10X",
        "target_bases_250X",
        "target_bases_500X",
        "median_coverage",
        "mean_insert_size",
        "fold_80",
        always=True,
        allow_reuse=True,
    )(validate_float)


class SampleModel(BaseModel):
    """
    Sample attributes model

    Attributes:
        name: sample name; source: LIMS/sample/name
        id: sample internal ID; source: StatusDB/sample/internal_id
        ticket: ticket number; source: StatusDB/sample/ticket_number
        status: sample status provided by the customer; MIP specific; source: StatusDB/family-sample/status
        gender: sample gender provided by the customer; source: LIMS/sample/sex
        source: sample type/source; source: LIMS/sample/source
        tumour: whether the sample is a tumour or normal one; BALSAMIC specific; source: StatusDB/sample/is_tumour
        application: analysis application model
        methods: sample processing methods model
        metadata: sample associated metrics and trending data model
        timestamp: processing timestamp attributes
    """

    name: str
    id: str
    ticket: Union[int, str]
    status: Optional[str]
    gender: Optional[str] = Gender.UNKNOWN
    source: Optional[str]
    tumour: Union[bool, str] = None
    application: ApplicationModel
    methods: MethodsModel
    metadata: MetadataModel
    timestamp: TimestampModel

    _tumour = validator("tumour", always=True, allow_reuse=True)(validate_boolean)
    _values = validator(
        "name", "id", "ticket", "status", "gender", "source", always=True, allow_reuse=True
    )(validate_empty_field)
