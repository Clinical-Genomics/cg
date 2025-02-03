import pytest

from cg.models.orders.sample_base import ContainerEnum, SexEnum, StatusEnum
from cg.services.orders.validation.errors.case_sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    BufferMissingError,
    ConcentrationRequiredIfSkipRCError,
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    InvalidBufferError,
    InvalidConcentrationIfSkipRCError,
    InvalidVolumeError,
    OccupiedWellError,
    SampleDoesNotExistError,
    SampleNameRepeatedError,
    SampleNameSameAsCaseNameError,
    SampleOutsideOfCollaborationError,
    SexSubjectIdError,
    StatusUnknownError,
    SubjectIdSameAsCaseNameError,
    SubjectIdSameAsSampleNameError,
    VolumeRequiredError,
    WellFormatError,
    WellPositionMissingError,
)
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.rules.case_sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_required,
    validate_buffers_are_allowed,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_container_name_required,
    validate_existing_samples_belong_to_collaboration,
    validate_not_all_samples_unknown_in_case,
    validate_sample_names_different_from_case_names,
    validate_sample_names_not_repeated,
    validate_samples_exist,
    validate_subject_ids_different_from_case_names,
    validate_subject_ids_different_from_sample_names,
    validate_subject_sex_consistency,
    validate_tube_container_name_unique,
    validate_volume_interval,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
)
from cg.services.orders.validation.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.orders.validation.workflows.tomte.models.order import TomteOrder
from cg.services.orders.validation.workflows.tomte.models.sample import TomteSample
from cg.store.models import Application, Sample
from cg.store.store import Store


def test_validate_well_position_format(valid_order: OrderWithCases):

    # GIVEN an order with invalid well position format
    valid_order.cases[0].samples[0].well_position = "D:0"

    # WHEN validating the well position format
    errors: list[WellFormatError] = validate_well_position_format(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid well position format
    assert isinstance(errors[0], WellFormatError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0


def test_validate_tube_container_name_unique(valid_order: OrderWithCases):

    # GIVEN an order with two samples with the same tube container name
    valid_order.cases[0].samples[0].container = ContainerEnum.tube
    valid_order.cases[0].samples[1].container = ContainerEnum.tube
    valid_order.cases[0].samples[0].container_name = "tube_name"
    valid_order.cases[0].samples[1].container_name = "tube_name"

    # WHEN validating the tube container name uniqueness
    errors: list[ContainerNameRepeatedError] = validate_tube_container_name_unique(
        order=valid_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the non-unique tube container name
    assert isinstance(errors[0], ContainerNameRepeatedError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0


def test_applications_exist(valid_order: OrderWithCases, base_store: Store):
    # GIVEN an order where one of the samples has an invalid application
    for case in valid_order.cases:
        case.samples[0].application = "Invalid application"

    # WHEN validating the order
    errors: list[ApplicationNotValidError] = validate_application_exists(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the ticket number
    assert isinstance(errors[0], ApplicationNotValidError)


def test_applications_not_archived(
    valid_order: OrderWithCases, base_store: Store, archived_application: Application
):
    # GIVEN an order where one of the samples has an invalid application
    base_store.session.add(archived_application)
    base_store.commit_to_store()
    for case in valid_order.cases:
        case.samples[0].application = archived_application.tag

    # WHEN validating the order
    errors: list[ApplicationArchivedError] = validate_application_not_archived(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the archived application
    assert isinstance(errors[0], ApplicationArchivedError)


def test_missing_required_volume(valid_order: OrderWithCases):

    # GIVEN an orders with two samples with missing volumes
    valid_order.cases[0].samples[0].container = ContainerEnum.tube
    valid_order.cases[0].samples[0].volume = None

    valid_order.cases[0].samples[1].container = ContainerEnum.plate
    valid_order.cases[0].samples[1].volume = None

    # WHEN validating that required volumes are set
    errors: list[VolumeRequiredError] = validate_volume_required(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the errors should concern the missing volumes
    assert isinstance(errors[0], VolumeRequiredError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0

    assert isinstance(errors[1], VolumeRequiredError)
    assert errors[1].sample_index == 1 and errors[1].case_index == 0


def test_sample_internal_ids_does_not_exist(
    valid_order: OrderWithCases,
    base_store: Store,
    store_with_multiple_cases_and_samples: Store,
):

    # GIVEN an order with a sample marked as existing but which does not exist in the database
    existing_sample = ExistingSample(internal_id="Non-existent sample", status=StatusEnum.unknown)
    valid_order.cases[0].samples.append(existing_sample)

    # WHEN validating that the samples exists
    errors: list[SampleDoesNotExistError] = validate_samples_exist(
        order=valid_order, store=store_with_multiple_cases_and_samples
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the non-existent sample
    assert isinstance(errors[0], SampleDoesNotExistError)


def test_application_is_incompatible(
    valid_order: TomteOrder, sample_with_non_compatible_application: TomteSample, base_store: Store
):

    # GIVEN an order that has a sample with an application which is incompatible with the workflow
    valid_order.cases[0].samples.append(sample_with_non_compatible_application)

    # WHEN validating the order
    errors: list[ApplicationNotCompatibleError] = validate_application_compatibility(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the application compatability
    assert isinstance(errors[0], ApplicationNotCompatibleError)


def test_subject_ids_same_as_case_names_not_allowed(valid_order: TomteOrder):

    # GIVEN an order with a sample having its subject_id same as the case's name
    case_name = valid_order.cases[0].name
    valid_order.cases[0].samples[0].subject_id = case_name

    # WHEN validating that no subject ids are the same as the case name
    errors: list[SubjectIdSameAsCaseNameError] = validate_subject_ids_different_from_case_names(
        valid_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should be concerning the subject id being the same as the case name
    assert isinstance(errors[0], SubjectIdSameAsCaseNameError)


def test_well_position_missing(
    valid_order: TomteOrder, sample_with_missing_well_position: TomteSample
):
    # GIVEN an order with a sample with a missing well position
    valid_order.cases[0].samples.append(sample_with_missing_well_position)

    # WHEN validating that no well positions are missing
    errors: list[WellPositionMissingError] = validate_well_positions_required(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing well position
    assert isinstance(errors[0], WellPositionMissingError)


def test_container_name_missing(
    valid_order: TomteOrder, sample_with_missing_container_name: TomteSample
):

    # GIVEN an order with a sample missing its container name
    valid_order.cases[0].samples.append(sample_with_missing_container_name)

    # WHEN validating that it is not missing any container names
    errors: list[ContainerNameMissingError] = validate_container_name_required(order=valid_order)

    # THEN an error should be raised
    assert errors

    # THEN the error should concern the missing container name
    assert isinstance(errors[0], ContainerNameMissingError)


@pytest.mark.parametrize("sample_volume", [1, 200], ids=["Too low", "Too high"])
def test_volume_out_of_bounds(valid_order: TomteOrder, sample_volume: int):

    # GIVEN an order containing a sample with an invalid volume
    valid_order.cases[0].samples[0].volume = sample_volume

    # WHEN validating that the volume is within bounds
    errors: list[InvalidVolumeError] = validate_volume_interval(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid volume
    assert isinstance(errors[0], InvalidVolumeError)


def test_multiple_samples_in_well_not_allowed(order_with_samples_in_same_well: OrderWithCases):

    # GIVEN an order with multiple samples in the same well

    # WHEN validating the order
    errors: list[OccupiedWellError] = validate_wells_contain_at_most_one_sample(
        order_with_samples_in_same_well
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the well
    assert isinstance(errors[0], OccupiedWellError)


def test_repeated_sample_names_not_allowed(
    order_with_repeated_sample_names: OrderWithCases, base_store: Store
):
    # GIVEN an order with samples in a case with the same name

    # WHEN validating the order
    errors: list[SampleNameRepeatedError] = validate_sample_names_not_repeated(
        order=order_with_repeated_sample_names, store=base_store
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the sample names
    assert isinstance(errors[0], SampleNameRepeatedError)


def test_elution_buffer_is_not_allowed(valid_order: TomteOrder):

    # GIVEN an order with 'skip reception control' toggled but no buffers specfied
    valid_order.skip_reception_control = True

    # WHEN validating that the buffers conform to the 'skip reception control' requirements
    errors: list[InvalidBufferError] = validate_buffers_are_allowed(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the buffer compatability
    assert isinstance(errors[0], InvalidBufferError)


def test_subject_id_same_as_sample_name_is_not_allowed(valid_order: TomteOrder):

    # GIVEN an order with a sample with same name and subject id
    sample_name = valid_order.cases[0].samples[0].name
    valid_order.cases[0].samples[0].subject_id = sample_name

    # WHEN validating that the subject ids are different from the sample names
    errors: list[SubjectIdSameAsSampleNameError] = validate_subject_ids_different_from_sample_names(
        valid_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the subject id being the same as the sample name
    assert isinstance(errors[0], SubjectIdSameAsSampleNameError)


def test_concentration_required_if_skip_rc(valid_order: OrderWithCases):
    # GIVEN an order with missing concentration trying to skip reception control
    valid_order.skip_reception_control = True

    # WHEN validating that concentration is provided
    errors: list[ConcentrationRequiredIfSkipRCError] = validate_concentration_required_if_skip_rc(
        valid_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing concentration
    assert isinstance(errors[0], ConcentrationRequiredIfSkipRCError)


def test_concentration_not_within_interval_if_skip_rc(
    order_with_invalid_concentration: TomteOrder,
    sample_with_invalid_concentration: TomteSample,
    base_store: Store,
    application_with_concentration_interval: Application,
):

    # GIVEN an order skipping reception control
    # GIVEN that the order has a sample with invalid concentration for its application
    base_store.session.add(application_with_concentration_interval)
    base_store.session.commit()

    # WHEN validating that the concentration is within the allowed interval
    errors: list[InvalidConcentrationIfSkipRCError] = validate_concentration_interval_if_skip_rc(
        order=order_with_invalid_concentration, store=base_store
    )

    # THEN an error is returned
    assert errors

    # THEN the error should concern the application interval
    assert isinstance(errors[0], InvalidConcentrationIfSkipRCError)


def test_missing_volume_no_container(valid_order: OrderWithCases):

    # GIVEN an order with a sample with missing volume, but which is in no container
    valid_order.cases[0].samples[0].container = ContainerEnum.no_container
    valid_order.cases[0].samples[0].volume = None

    # WHEN validating that the order has required volumes set
    errors: list[VolumeRequiredError] = validate_volume_required(order=valid_order)

    # THEN no error should be returned
    assert not errors


def test_validate_sex_subject_id_clash(valid_order: OrderWithCases, sample_store: Store):
    # GIVEN an existing sample
    sample = sample_store.session.query(Sample).first()

    # GIVEN an order and sample with the same customer and subject id
    valid_order.customer = sample.customer.internal_id
    valid_order.cases[0].samples[0].subject_id = "subject"
    sample.subject_id = "subject"

    # GIVEN a sample in the order that has a different sex
    valid_order.cases[0].samples[0].sex = SexEnum.female
    sample.sex = SexEnum.male

    # WHEN validating the order
    errors: list[SexSubjectIdError] = validate_subject_sex_consistency(
        order=valid_order,
        store=sample_store,
    )

    # THEN an error should be given for the clash
    assert errors
    assert isinstance(errors[0], SexSubjectIdError)


def test_validate_sex_subject_id_no_clash(valid_order: OrderWithCases, sample_store: Store):
    # GIVEN an existing sample
    sample = sample_store.session.query(Sample).first()

    # GIVEN an order and sample with the same customer and subject id
    valid_order.customer = sample.customer.internal_id
    valid_order.cases[0].samples[0].subject_id = "subject"
    sample.subject_id = "subject"

    # GIVEN that the order's sample has a matching sex to the one in StatusDB
    valid_order.cases[0].samples[0].sex = SexEnum.female
    sample.sex = SexEnum.female

    # WHEN validating the order
    errors: list[SexSubjectIdError] = validate_subject_sex_consistency(
        order=valid_order,
        store=sample_store,
    )

    # THEN no error should be returned
    assert not errors


def test_validate_sex_subject_id_existing_sex_unknown(
    valid_order: OrderWithCases, sample_store: Store
):
    # GIVEN an existing sample
    sample = sample_store.session.query(Sample).first()

    # GIVEN an order and sample with the same customer and subject id
    valid_order.customer = sample.customer.internal_id
    valid_order.cases[0].samples[0].subject_id = "subject"
    sample.subject_id = "subject"

    # GIVEN a sample in the order that has a known sex and the existing sample's sex is unknown
    valid_order.cases[0].samples[0].sex = SexEnum.female
    sample.sex = SexEnum.unknown

    # WHEN validating the order
    errors: list[SexSubjectIdError] = validate_subject_sex_consistency(
        order=valid_order,
        store=sample_store,
    )

    # THEN no error should be returned
    assert not errors


def test_validate_sex_subject_id_new_sex_unknown(valid_order: OrderWithCases, sample_store: Store):
    # GIVEN an existing sample
    sample = sample_store.session.query(Sample).first()

    # GIVEN an order and sample with the same customer and subject id
    valid_order.customer = sample.customer.internal_id
    valid_order.cases[0].samples[0].subject_id = "subject"
    sample.subject_id = "subject"

    # GIVEN a sample in the order that has an unknown sex and the existing sample's sex is known
    valid_order.cases[0].samples[0].sex = SexEnum.unknown
    sample.sex = SexEnum.female

    # WHEN validating the order
    errors: list[SexSubjectIdError] = validate_subject_sex_consistency(
        order=valid_order,
        store=sample_store,
    )

    # THEN no error should be returned
    assert not errors


def test_validate_sample_names_different_from_case_names(
    order_with_samples_having_same_names_as_cases: OrderWithCases, base_store: Store
):
    # GIVEN an order with a case holding samples with the same name as cases in the order

    # WHEN validating that the sample names are different from the case names
    errors: list[SampleNameSameAsCaseNameError] = validate_sample_names_different_from_case_names(
        order=order_with_samples_having_same_names_as_cases, store=base_store
    )

    # THEN a list with two errors should be returned
    assert len(errors) == 2

    # THEN the errors should concern the same case and sample name and hold the correct indices
    for error in errors:
        assert isinstance(error, SampleNameSameAsCaseNameError)
        assert error.case_index == 0

    assert errors[0].sample_index == 0
    assert errors[1].sample_index == 1


def test_validate_sample_names_different_from_existing_case_names(
    valid_order: TomteOrder, store_with_multiple_cases_and_samples: Store
):
    # GIVEN an order with a case holding samples with the same name as an existing case in the order
    case = store_with_multiple_cases_and_samples.get_cases()[0]
    existing_case = ExistingCase(internal_id=case.internal_id, panels=case.panels)
    valid_order.cases.append(existing_case)
    valid_order.cases[0].samples[0].name = case.name

    # WHEN validating that the sample names are different from the case names
    errors: list[SampleNameSameAsCaseNameError] = validate_sample_names_different_from_case_names(
        order=valid_order, store=store_with_multiple_cases_and_samples
    )

    # THEN a list with one error should be returned
    assert len(errors) == 1

    # THEN the errors should concern the same case and sample name and hold the correct indices
    error = errors[0]
    assert isinstance(error, SampleNameSameAsCaseNameError)
    assert error.case_index == 0
    assert error.sample_index == 0


def test_validate_not_all_samples_unknown_in_case(valid_order: OrderWithCases):

    # GIVEN an order with a case with all samples unknown
    for sample in valid_order.cases[0].samples:
        sample.status = StatusEnum.unknown

    # WHEN validating that not all samples are unknown in a case
    errors: list[StatusUnknownError] = validate_not_all_samples_unknown_in_case(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the case with all samples unknown
    assert isinstance(errors[0], StatusUnknownError)


def test_validate_buffer_required(mip_dna_order: MipDnaOrder, application_tag_required_buffer: str):

    # GIVEN an order for which the buffer is only required for samples running certain applications

    # GIVEN that one of its samples has an app tag which makes the elution buffer mandatory
    sample = mip_dna_order.cases[0].samples[0]
    sample.application = application_tag_required_buffer

    # GIVEN that the sample has no buffer set
    sample.elution_buffer = None

    # WHEN validating that required buffers are set
    errors: list[BufferMissingError] = validate_buffer_required(mip_dna_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing buffer
    error = errors[0]
    assert isinstance(error, BufferMissingError)
    assert error.sample_index == 0 and error.case_index == 0


def test_existing_sample_from_outside_of_collaboration(
    mip_dna_order: MipDnaOrder,
    store_with_multiple_cases_and_samples: Store,
    sample_id_in_single_case: str,
):

    # GIVEN a customer from outside the order's customer's collaboration
    new_customer = store_with_multiple_cases_and_samples.add_customer(
        internal_id="NewCustomer",
        name="New customer",
        invoice_address="Test street",
        invoice_reference="Invoice reference",
    )
    store_with_multiple_cases_and_samples.add_item_to_store(new_customer)
    store_with_multiple_cases_and_samples.commit_to_store()

    # GIVEN a sample belonging to the customer is added to the order
    sample: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        sample_id_in_single_case
    )
    sample.customer = new_customer
    existing_sample = ExistingSample(internal_id=sample.internal_id)
    mip_dna_order.cases[0].samples.append(existing_sample)

    # WHEN validating that the order does not contain samples from outside the customer's collaboration
    errors: list[SampleOutsideOfCollaborationError] = (
        validate_existing_samples_belong_to_collaboration(
            order=mip_dna_order, store=store_with_multiple_cases_and_samples
        )
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the added existing case
    assert isinstance(errors[0], SampleOutsideOfCollaborationError)
