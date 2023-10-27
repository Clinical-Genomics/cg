from typing import Optional, Union

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated

from cg.constants import NA_FIELD
from cg.models.report.metadata import (
    BalsamicTargetedSampleMetadataModel,
    BalsamicWGSSampleMetadataModel,
    MipDNASampleMetadataModel,
    RnafusionSampleMetadataModel,
)
from cg.models.report.validators import (
    get_boolean_as_string,
    get_date_as_string,
    get_gender_as_string,
    get_prep_category_as_string,
    get_report_string,
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

    tag: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    version: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    prep_category: Annotated[str, BeforeValidator(get_prep_category_as_string)] = NA_FIELD
    description: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    details: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    limitations: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    pipeline_limitations: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    accredited: Optional[bool] = None
    external: Optional[bool] = None


class MethodsModel(BaseModel):
    """
    Model describing the methods used for preparation and sequencing of the samples

    Attributes:
        library_prep: library preparation method; source: LIMS/sample/prep_method
        sequencing: sequencing procedure; source: LIMS/sample/sequencing_method
    """

    library_prep: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    sequencing: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD


class TimestampModel(BaseModel):
    """
    Model describing the processing timestamps of a specific sample

    Atributes:
        ordered_at: order date; source: StatusDB/sample/ordered_at
        received_at: arrival date; source: StatusDB/sample/received_at
        prepared_at: library preparation date; source: StatusDB/sample/prepared_at
        reads_updated_at: sequencing date; source: StatusDB/sample/reads_updated_at
    """

    ordered_at: Annotated[str, BeforeValidator(get_date_as_string)] = NA_FIELD
    received_at: Annotated[str, BeforeValidator(get_date_as_string)] = NA_FIELD
    prepared_at: Annotated[str, BeforeValidator(get_date_as_string)] = NA_FIELD
    reads_updated_at: Annotated[str, BeforeValidator(get_date_as_string)] = NA_FIELD


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

    name: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    id: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    ticket: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    status: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    gender: Annotated[str, BeforeValidator(get_gender_as_string)] = NA_FIELD
    source: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    tumour: Annotated[str, BeforeValidator(get_boolean_as_string)] = NA_FIELD
    application: ApplicationModel
    methods: MethodsModel
    metadata: Union[
        MipDNASampleMetadataModel,
        BalsamicTargetedSampleMetadataModel,
        BalsamicWGSSampleMetadataModel,
        RnafusionSampleMetadataModel,
    ]
    timestamps: TimestampModel
