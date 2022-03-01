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
    version: Union[None, int, str]
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

    ordered_at: Union[None, datetime, str]
    received_at: Union[None, datetime, str]
    prepared_at: Union[None, datetime, str]
    sequenced_at: Union[None, datetime, str]
    delivered_at: Union[None, datetime, str]
    processing_days: Union[None, int, str]

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
        bait_set: panel bed used for the analysis; StatusDB/sample/capture_kit
        bait_set_version: panel bed version; BALSAMIC specific; source: pipeline workflow
        gender: gender estimated by the pipeline; source: pipeline workflow
        million_read_pairs: number of million read pairs obtained; source: StatusDB/sample/reads (/2*10^6)
        mapped_reads: percentage of reads aligned to the reference sequence; MIP specific; source: pipeline workflow
        duplicates: fraction of mapped sequence that is marked as duplicate; source: pipeline workflow
        target_coverage: mean coverage of a target region; MIP specific; source: pipeline workflow
        target_bases_10X: percent of targeted bases that are covered to 10X coverage or more; MIP specific; source: pipeline workflow
        target_bases_250X: percent of targeted bases that are covered to 250X coverage or more; BALSAMIC specific; source: pipeline workflow
        target_bases_500X: percent of targeted bases that are covered to 500X coverage or more; BALSAMIC specific; source: pipeline workflow
        median_coverage: median coverage in bases; source: pipeline workflow
        mean_insert_size: mean insert size of the distribution; BALSAMIC specific; source: pipeline workflow
        fold_80: fold 80 base penalty; BALSAMIC specific; source: pipeline workflow
    """

    bait_set: Optional[str]
    bait_set_version: Optional[str]
    gender: Optional[str]
    million_read_pairs: Union[None, float, str]
    mapped_reads: Union[None, float, str]
    duplicates: Union[None, float, str]
    target_coverage: Union[None, float, str]
    target_bases_10X: Union[None, float, str]
    target_bases_250X: Union[None, float, str]
    target_bases_500X: Union[None, float, str]
    median_coverage: Union[None, float, str]
    mean_insert_size: Union[None, float, str]
    fold_80: Union[None, float, str]

    _str_values = validator(
        "bait_set", "bait_set_version", "gender", always=True, allow_reuse=True
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
    tumour: Union[None, bool, str]
    application: ApplicationModel
    methods: MethodsModel
    metadata: MetadataModel
    timestamp: TimestampModel

    _tumour = validator("tumour", always=True, allow_reuse=True)(validate_boolean)
    _values = validator(
        "name", "id", "ticket", "status", "gender", "source", always=True, allow_reuse=True
    )(validate_empty_field)
