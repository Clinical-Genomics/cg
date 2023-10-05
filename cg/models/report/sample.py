from typing import Optional

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated

from cg.models.report.metadata import SampleMetadataModel
from cg.models.report.validators import (
    validate_boolean,
    validate_date,
    validate_empty_field,
    validate_gender,
    validate_rml_sample,
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

    tag: Annotated[str, BeforeValidator(validate_empty_field)]
    version: Annotated[str, BeforeValidator(validate_empty_field)]
    prep_category: Annotated[str, BeforeValidator(validate_rml_sample)]
    description: Annotated[str, BeforeValidator(validate_empty_field)]
    limitations: Annotated[str, BeforeValidator(validate_empty_field)]
    accredited: Optional[bool] = None
    external: Optional[bool] = None


class MethodsModel(BaseModel):
    """
    Model describing the methods used for preparation and sequencing of the samples

    Attributes:
        library_prep: library preparation method; source: LIMS/sample/prep_method
        sequencing: sequencing procedure; source: LIMS/sample/sequencing_method
    """

    library_prep: Annotated[str, BeforeValidator(validate_empty_field)]
    sequencing: Annotated[str, BeforeValidator(validate_empty_field)]


class TimestampModel(BaseModel):
    """
    Model describing the processing timestamps of a specific sample

    Atributes:
        ordered_at: order date; source: StatusDB/sample/ordered_at
        received_at: arrival date; source: StatusDB/sample/received_at
        prepared_at: library preparation date; source: StatusDB/sample/prepared_at
        reads_updated_at: sequencing date; source: StatusDB/sample/reads_updated_at
    """

    ordered_at: Annotated[str, BeforeValidator(validate_date)]
    received_at: Annotated[str, BeforeValidator(validate_date)]
    prepared_at: Annotated[str, BeforeValidator(validate_date)]
    reads_updated_at: Annotated[str, BeforeValidator(validate_date)]


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

    name: Annotated[str, BeforeValidator(validate_empty_field)]
    id: Annotated[str, BeforeValidator(validate_empty_field)]
    ticket: Annotated[str, BeforeValidator(validate_empty_field)]
    status: Annotated[str, BeforeValidator(validate_empty_field)]
    gender: Annotated[str, BeforeValidator(validate_gender)]
    source: Annotated[str, BeforeValidator(validate_empty_field)]
    tumour: Annotated[str, BeforeValidator(validate_boolean)]
    application: ApplicationModel
    methods: MethodsModel
    metadata: SampleMetadataModel
    timestamps: TimestampModel
