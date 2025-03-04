from cg.server.dto.samples.samples_response import (
    ApplicationDTO,
    ApplicationVersionDTO,
    CustomerDto,
    SampleDTO,
)
from cg.store.models import Application, ApplicationVersion, Sample


def create_sample_dto(sample: Sample) -> SampleDTO:
    customer = create_customer_dto(sample)
    application = create_application_dto(sample.application_version.application)
    application_version = create_application_version_dto(sample.application_version)

    return SampleDTO(
        comment=sample.comment,
        control=sample.control,
        customer=customer,
        internal_id=sample.internal_id,
        name=sample.name,
        phenotype_groups=sample.phenotype_groups,
        phenotype_terms=sample.phenotype_terms,
        priority=sample.priority_human,
        reference_genome=sample.reference_genome,
        subject_id=sample.subject_id,
        is_tumour=sample.is_tumour,
        application=application,
        application_version=application_version,
        sex=sample.sex,
    )


def create_customer_dto(sample: Sample) -> CustomerDto:
    return CustomerDto(
        internal_id=sample.customer.internal_id,
        name=sample.customer.name,
    )


def create_application_dto(application: Application) -> ApplicationDTO:
    return ApplicationDTO(
        id=application.id,
        tag=application.tag,
        prep_category=application.prep_category,
        is_external=application.is_external,
        description=application.description,
        is_accredited=application.is_accredited,
        turnaround_time=application.turnaround_time,
        minimum_order=application.minimum_order,
        sequencing_depth=application.sequencing_depth,
        min_sequencing_depth=application.min_sequencing_depth,
        target_reads=application.target_reads,
        percent_reads_guaranteed=application.percent_reads_guaranteed,
        sample_amount=application.sample_amount,
        sample_volume=application.sample_volume,
        sample_concentration=application.sample_concentration,
        sample_concentration_minimum=application.sample_concentration_minimum,
        sample_concentration_maximum=application.sample_concentration_maximum,
        sample_concentration_minimum_cfdna=application.sample_concentration_minimum_cfdna,
        sample_concentration_maximum_cfdna=application.sample_concentration_maximum_cfdna,
        priority_processing=application.priority_processing,
        details=application.details,
        limitations=application.details,
        percent_kth=application.percent_kth,
        comment=application.comment,
        is_archived=application.is_archived,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def create_application_version_dto(version: ApplicationVersion) -> ApplicationVersionDTO:
    return ApplicationVersionDTO(
        id=version.id,
        version=version.version,
        valid_from=version.valid_from,
        price_standard=version.price_standard,
        price_priority=version.price_priority,
        price_express=version.price_express,
        price_research=version.price_research,
        price_clinical_trials=version.price_clinical_trials,
        comment=version.comment,
        created_at=version.created_at,
        updated_at=version.updated_at,
        application_id=version.application_id,
    )
