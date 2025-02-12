from cg.models.orders.sample_base import ContainerEnum, ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import ElutionBuffer, IndexEnum
from cg.services.orders.validation.errors.sample_errors import (
    BufferInvalidError,
    ConcentrationInvalidIfSkipRCError,
    ConcentrationRequiredError,
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    IndexNumberMissingError,
    IndexNumberOutOfRangeError,
    IndexSequenceMismatchError,
    IndexSequenceMissingError,
    PoolApplicationError,
    PoolPriorityError,
    SampleNameNotAvailableControlError,
    SampleNameNotAvailableError,
    VolumeRequiredError,
    WellFormatError,
    WellFormatRmlError,
)
from cg.services.orders.validation.index_sequences import INDEX_SEQUENCES
from cg.services.orders.validation.rules.sample.rules import (
    validate_buffer_skip_rc_condition,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_container_name_required,
    validate_index_number_in_range,
    validate_index_number_required,
    validate_index_sequence_mismatch,
    validate_index_sequence_required,
    validate_non_control_sample_names_available,
    validate_pools_contain_one_application,
    validate_pools_contain_one_priority,
    validate_sample_names_available,
    validate_tube_container_name_unique,
    validate_volume_required,
    validate_well_position_format,
    validate_well_position_rml_format,
)
from cg.services.orders.validation.workflows.fastq.models.order import FastqOrder
from cg.services.orders.validation.workflows.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.workflows.mutant.models.order import MutantOrder
from cg.services.orders.validation.workflows.rml.models.order import RMLOrder
from cg.services.orders.validation.workflows.rml.models.sample import RMLSample
from cg.store.models import Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_sample_names_available(valid_microsalt_order: MicrosaltOrder, sample_store: Store):

    # GIVEN an order with a sample name reused from a previous order
    sample = sample_store.session.query(Sample).first()
    valid_microsalt_order.customer = sample.customer.internal_id
    valid_microsalt_order.samples[0].name = sample.name

    # WHEN validating that the sample names are available to the customer
    errors = validate_sample_names_available(order=valid_microsalt_order, store=sample_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the reused sample name
    assert isinstance(errors[0], SampleNameNotAvailableError)


def test_validate_tube_container_name_unique(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with three samples in tubes with 2 reused container names
    valid_microsalt_order.samples[0].container = ContainerEnum.tube
    valid_microsalt_order.samples[1].container = ContainerEnum.tube
    valid_microsalt_order.samples[2].container = ContainerEnum.tube
    valid_microsalt_order.samples[0].container_name = "container_name"
    valid_microsalt_order.samples[1].container_name = "container_name"
    valid_microsalt_order.samples[2].container_name = "ContainerName"

    # WHEN validating the container names are unique
    errors = validate_tube_container_name_unique(order=valid_microsalt_order)

    # THEN the error should concern the reused container name
    assert isinstance(errors[0], ContainerNameRepeatedError)
    assert errors[0].sample_index == 0
    assert errors[1].sample_index == 1


def test_validate_sample_names_available(
    fluffy_order: FluffyOrder, store: Store, helpers: StoreHelpers
):
    """
    Test that an order without any control sample that has a sample name already existing in the
    database returns an error.
    """

    # GIVEN an order without control with a sample name already in the database
    sample_name: str = fluffy_order.samples[0].name
    helpers.add_sample(
        store=store,
        name=sample_name,
        customer_id=fluffy_order.customer,
    )

    # WHEN validating that the sample names are available to the customer
    errors = validate_sample_names_available(order=fluffy_order, store=store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the reused sample name
    assert isinstance(errors[0], SampleNameNotAvailableError)


def test_validate_non_control_sample_names_available(
    mutant_order: MutantOrder, store: Store, helpers: StoreHelpers
):
    """
    Test that an order with a control sample name already existing in the database returns no error.
    """

    # GIVEN an order with a control sample
    sample = mutant_order.samples[0]
    assert sample.control == ControlEnum.positive

    # GIVEN that there is a sample in the database with the same name
    helpers.add_sample(
        store=store,
        name=sample.name,
        customer_id=mutant_order.customer,
    )

    # WHEN validating that the sample names are available to the customer
    errors = validate_non_control_sample_names_available(order=mutant_order, store=store)

    # THEN no error should be returned because it is a control sample
    assert not errors


def test_validate_non_control_sample_names_available_non_control_sample_name(
    mutant_order: MutantOrder, store: Store, helpers: StoreHelpers
):
    """
    Test that an order with a non-control sample name already existing in the database returns an
    error.
    """

    # GIVEN an order with a non-control sample
    sample = mutant_order.samples[2]
    assert sample.control == ControlEnum.not_control

    # GIVEN that there is a sample in the database with the same name
    helpers.add_sample(
        store=store,
        name=sample.name,
        customer_id=mutant_order.customer,
    )

    # WHEN validating that the sample names are available to the customer
    errors = validate_non_control_sample_names_available(order=mutant_order, store=store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the reused sample name
    assert isinstance(errors[0], SampleNameNotAvailableControlError)


def test_validate_well_position_format(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with a sample with an invalid well position
    valid_microsalt_order.samples[0].well_position = "J:4"

    # WHEN validating the well position format
    errors = validate_well_position_format(order=valid_microsalt_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid well position
    assert isinstance(errors[0], WellFormatError)
    assert errors[0].sample_index == 0


def test_validate_well_position_rml_format(rml_order: RMLOrder):

    # GIVEN a RML order with a sample with an invalid well position
    rml_order.samples[0].well_position_rml = "J:4"

    # WHEN validating the well position format
    errors = validate_well_position_rml_format(order=rml_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid well position
    assert isinstance(errors[0], WellFormatRmlError)
    assert errors[0].sample_index == 0


def test_validate_missing_container_name(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with a sample on a plate with no container name
    valid_microsalt_order.samples[0].container = ContainerEnum.plate
    valid_microsalt_order.samples[0].container_name = None

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_microsalt_order)

    # THEN am error should be returned
    assert errors

    # THEN the error should concern the missing container name
    assert isinstance(errors[0], ContainerNameMissingError)
    assert errors[0].sample_index == 0


def test_validate_valid_container_name(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with a sample on a plate with a valid container name
    valid_microsalt_order.samples[0].container = ContainerEnum.plate
    valid_microsalt_order.samples[0].container_name = "Plate_123"

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_microsalt_order)

    # THEN no error should be returned
    assert not errors


def test_validate_non_plate_container(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with missing container names but the samples are not on plates
    valid_microsalt_order.samples[0].container = ContainerEnum.tube
    valid_microsalt_order.samples[0].container_name = None

    valid_microsalt_order.samples[1].container = ContainerEnum.no_container
    valid_microsalt_order.samples[1].container_name = None

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_microsalt_order)

    # THEN no error should be returned
    assert not errors


def test_missing_required_sample_volume(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with containerized samples missing volume
    valid_microsalt_order.samples[0].container = ContainerEnum.tube
    valid_microsalt_order.samples[0].volume = None

    valid_microsalt_order.samples[1].container = ContainerEnum.plate
    valid_microsalt_order.samples[1].volume = None

    # WHEN validating the volume
    errors = validate_volume_required(order=valid_microsalt_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing volume
    assert isinstance(errors[0], VolumeRequiredError)
    assert errors[0].sample_index == 0

    assert isinstance(errors[1], VolumeRequiredError)
    assert errors[1].sample_index == 1


def test_non_required_sample_volume(valid_microsalt_order: MicrosaltOrder):

    # GIVEN an order with a sample not in a container and no volume set
    valid_microsalt_order.samples[0].container = ContainerEnum.no_container
    valid_microsalt_order.samples[0].volume = None

    # WHEN validating the volume
    errors = validate_volume_required(order=valid_microsalt_order)

    # THEN no error should be returned
    assert not errors


def test_validate_concentration_required_if_skip_rc(fastq_order: FastqOrder):

    # GIVEN a fastq order trying to skip reception control
    fastq_order.skip_reception_control = True

    # GIVEN that one of its samples has no concentration set
    fastq_order.samples[0].concentration_ng_ul = None

    # WHEN validating that the concentration is not missing
    errors: list[ConcentrationRequiredError] = validate_concentration_required_if_skip_rc(
        order=fastq_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing concentration
    assert isinstance(errors[0], ConcentrationRequiredError)


def test_validate_concentration_interval_if_skip_rc(fastq_order: FastqOrder, base_store: Store):

    # GIVEN a Fastq order trying to skip reception control
    fastq_order.skip_reception_control = True

    # GIVEN that one of the samples has a concentration outside the allowed interval for its
    # application
    sample = fastq_order.samples[0]
    application = base_store.get_application_by_tag(sample.application)
    application.sample_concentration_minimum = sample.concentration_ng_ul + 1
    base_store.session.add(application)
    base_store.commit_to_store()

    # WHEN validating that the order's samples' concentrations are within allowed intervals
    errors: list[ConcentrationInvalidIfSkipRCError] = validate_concentration_interval_if_skip_rc(
        order=fastq_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the concentration level
    assert isinstance(errors[0], ConcentrationInvalidIfSkipRCError)


def test_validate_buffer_skip_rc_condition(fastq_order: FastqOrder):

    # GIVEN a Fastq order trying to skip reception control
    fastq_order.skip_reception_control = True

    # GIVEN that one of the samples has buffer specified as 'other'
    fastq_order.samples[0].elution_buffer = ElutionBuffer.OTHER

    # WHEN validating that the buffers follow the 'skip reception control' requirements
    errors: list[BufferInvalidError] = validate_buffer_skip_rc_condition(order=fastq_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the buffer
    assert isinstance(errors[0], BufferInvalidError)


def test_validate_pools_contain_multiple_applications(rml_order: RMLOrder):

    # GIVEN a pooled order with the same pool containing multiple applications
    rml_order.samples[0].pool = "pool"
    rml_order.samples[1].pool = "pool"
    _, samples = next(iter(rml_order.pools.items()))
    samples[1].application = f"Not {samples[0].application}"

    # WHEN validating that the pools contain a single application
    errors: list[PoolApplicationError] = validate_pools_contain_one_application(rml_order)

    # THEN errors should be returned
    assert errors

    # THEN the errors should concern the pool with repeated applications
    assert isinstance(errors[0], PoolApplicationError)
    assert len(errors) == len(samples)


def test_validate_pools_contain_multiple_priorities(rml_order: RMLOrder):

    # GIVEN a pooled order with the same pool containing multiple priorities
    rml_order.samples[0].pool = "pool"
    rml_order.samples[1].pool = "pool"
    _, samples = next(iter(rml_order.pools.items()))
    samples[0].priority = PriorityEnum.research
    samples[1].priority = PriorityEnum.priority

    # WHEN validating that the pools contain a single application
    errors: list[PoolPriorityError] = validate_pools_contain_one_priority(rml_order)

    # THEN errors should be returned
    assert errors

    # THEN the errors should concern the pool with repeated applications
    assert isinstance(errors[0], PoolPriorityError)
    assert len(errors) == len(samples)


def test_validate_missing_index_number(rml_order: RMLOrder):

    # GIVEN an indexed order with a missing index number
    erroneous_sample: RMLSample = rml_order.samples[0]
    erroneous_sample.index = IndexEnum.AVIDA_INDEX_STRIP
    erroneous_sample.index_number = None

    # WHEN validating that no index numbers are missing
    errors: list[IndexNumberMissingError] = validate_index_number_required(rml_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the sample's missing index number
    assert isinstance(errors[0], IndexNumberMissingError)
    assert errors[0].sample_index == 0


def test_validate_index_number_out_of_range(rml_order: RMLOrder):

    # GIVEN an indexed order with an index number out of range
    erroneous_sample: RMLSample = rml_order.samples[0]
    erroneous_sample.index = IndexEnum.AVIDA_INDEX_STRIP
    erroneous_sample.index_number = len(INDEX_SEQUENCES[erroneous_sample.index]) + 1

    # WHEN validating that the index numbers are in range
    errors: list[IndexNumberOutOfRangeError] = validate_index_number_in_range(rml_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the sample's index number being out of range
    assert isinstance(errors[0], IndexNumberOutOfRangeError)
    assert errors[0].sample_index == 0


def test_validate_missing_index_sequence(rml_order: RMLOrder):

    # GIVEN an indexed order with a missing index sequence
    erroneous_sample: RMLSample = rml_order.samples[0]
    erroneous_sample.index = IndexEnum.AVIDA_INDEX_STRIP
    erroneous_sample.index_sequence = None

    # WHEN validating that no index sequences are missing
    errors: list[IndexSequenceMissingError] = validate_index_sequence_required(rml_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the sample's missing index sequence
    assert isinstance(errors[0], IndexSequenceMissingError)
    assert errors[0].sample_index == 0


def test_validate_index_sequence_mismatch(rml_order: RMLOrder):

    # GIVEN an indexed order with a mismatched index sequence
    erroneous_sample: RMLSample = rml_order.samples[0]
    erroneous_sample.index = IndexEnum.AVIDA_INDEX_STRIP
    erroneous_sample.index_number = 1
    erroneous_sample.index_sequence = INDEX_SEQUENCES[erroneous_sample.index][10]

    # WHEN validating that the index sequences match
    errors: list[IndexSequenceMismatchError] = validate_index_sequence_mismatch(rml_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the sample's mismatched index sequence
    assert isinstance(errors[0], IndexSequenceMismatchError)
    assert errors[0].sample_index == 0
