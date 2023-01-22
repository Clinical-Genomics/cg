from datetime import datetime
from typing import Optional, Union

from cg.constants.subject import Gender
from pydantic import BaseModel, validator
from cg.models.report.metadata import SampleMetadataModel
from cg.models.report.validators import (
    validate_empty_field,
    validate_boolean,
    validate_rml_sample,
    validate_date,
    validate_gender,
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
        accredited: if the sample associated process is accredited or not; source: StatusDB/application/is_accredited
        external: whether the app tag is external or not; source: StatusDB/application/is_external
    """

    tag: Optional[str]
    version: Union[None, int, str]
    prep_category: Optional[str]
    description: Optional[str]
    limitations: Optional[str]
    accredited: Optional[bool]
    external: Optional[bool]

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
    Model describing the processing timestamps of a specific sample

    Atributes:
        ordered_at: order date; source: StatusDB/sample/ordered_at
        received_at: arrival date; source: StatusDB/sample/received_at
        prepared_at: library preparation date; source: StatusDB/sample/prepared_at
        sequenced_at: sequencing date; source: StatusDB/sample/sequenced_at
    """

    ordered_at: Union[None, datetime, str]
    received_at: Union[None, datetime, str]
    prepared_at: Union[None, datetime, str]
    sequenced_at: Union[None, datetime, str]

    _values = validator(
        "ordered_at",
        "received_at",
        "prepared_at",
        "sequenced_at",
        always=True,
        allow_reuse=True,
    )(validate_date)


class SampleModel(BaseModel):
    """
    Sample attributes model

    Attributes:
        name: sample name; source: StatusDB/sample/name
        id: sample internal ID; source: StatusDB/sample/internal_id
        ticket: ticket number; source: StatusDB/sample/ticket_number
        status: sample status provided by the customer; source: StatusDB/family-sample/status
        gender: sample gender provided by the customer; source: StatusDB/sample/sex
        source: sample type/source; source: LIMS/sample/source
        tumour: whether the sample is a tumour or normal one; source: StatusDB/sample/is_tumour
        application: analysis application model
        methods: sample processing methods model
        metadata: sample associated metrics and trending data model
        timestamps: processing timestamp attributes
    """

    name: Optional[str]
    id: Optional[str]
    ticket: Union[None, int, str]
    status: Optional[str]
    gender: Optional[str] = Gender.UNKNOWN
    source: Optional[str]
    tumour: Union[None, bool, str]
    application: ApplicationModel
    methods: MethodsModel
    metadata: SampleMetadataModel
    timestamps: TimestampModel

    _tumour = validator("tumour", always=True, allow_reuse=True)(validate_boolean)
    _gender = validator("gender", always=True, allow_reuse=True)(validate_gender)
    _values = validator("name", "id", "ticket", "status", "source", always=True, allow_reuse=True)(
        validate_empty_field
    )
