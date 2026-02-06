from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.order_types.balsamic_umi.models.case import BalsamicUmiCase
from cg.services.orders.validation.order_types.balsamic_umi.models.sample import BalsamicUmiSample
from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample
from cg.services.orders.validation.order_types.raredisease.models.case import RarediseaseCase
from cg.services.orders.validation.order_types.raredisease.models.sample import RarediseaseSample
from cg.store.models import Application
from cg.store.models import Case as DbCase
from cg.store.models import Customer, Sample
from cg.store.store import Store


def contains_duplicates(input_list: list) -> bool:
    return len(set(input_list)) != len(input_list)


def is_double_tumour(case: BalsamicCase | BalsamicUmiCase, store: Store) -> bool:
    return len(case.samples) == 2 and get_number_of_tumours(case=case, store=store) == 2


def is_double_normal(case: BalsamicCase | BalsamicUmiCase, store: Store) -> bool:
    return len(case.samples) == 2 and get_number_of_tumours(case=case, store=store) == 0


def get_number_of_tumours(case: BalsamicCase | BalsamicUmiCase, store: Store) -> int:
    number_of_tumours = 0
    for sample in case.samples:
        if sample.is_new and sample.tumour:
            number_of_tumours += 1
        elif not sample.is_new:
            db_sample: Sample = store.get_sample_by_internal_id(sample.internal_id)
            if db_sample.is_tumour:
                number_of_tumours += 1
    return number_of_tumours


def is_normal_only_wgs(case: BalsamicCase | BalsamicUmiCase, store: Store) -> bool:
    return len(case.samples) == 1 and _is_sample_wgs_normal(sample=case.samples[0], store=store)


def _is_sample_wgs_normal(
    sample: BalsamicSample | BalsamicUmiSample | ExistingSample, store: Store
) -> bool:
    if sample.is_new:
        application: Application = store.get_application_by_tag(sample.application)
        return (
            application.prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            and not sample.tumour
        )
    else:
        db_sample: Sample = store.get_sample_by_internal_id(sample.internal_id)
        return (
            db_sample.prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            and not db_sample.is_tumour
        )


def is_case_not_from_collaboration(case: ExistingCase, customer_id: str, store: Store) -> bool:
    db_case: DbCase | None = store.get_case_by_internal_id(case.internal_id)
    customer: Customer | None = store.get_customer_by_internal_id(customer_id)
    return db_case and customer and db_case.customer not in customer.collaborators


def is_sample_in_case(case: Case, sample_name: str, store: Store) -> bool:
    if case.get_new_sample(sample_name):
        return True
    elif case.get_existing_sample_from_db(sample_name=sample_name, store=store):
        return True
    return False


def get_case_prep_categories(case: Case, store: Store) -> set[str]:
    """
    Return a set with all prep categories of the samples in the case
    if the sample and its application exist, and has a prep category.
    """
    prep_categories: set[str] = set()
    for _, sample in case.enumerated_new_samples:
        application: Application | None = store.get_application_by_tag(sample.application)
        if application and application.prep_category:
            prep_categories.add(application.prep_category)

    for _, sample in case.enumerated_existing_samples:
        db_sample: Sample | None = store.get_sample_by_internal_id(sample.internal_id)
        if db_sample and db_sample.prep_category:
            prep_categories.add(db_sample.prep_category)
    return prep_categories


def does_case_exist(case: MIPDNACase | RarediseaseCase | ExistingCase, store: Store):
    if isinstance(case, ExistingCase):
        return bool(store.get_case_by_internal_id(case.internal_id))
    return True


def is_single_sample_case(case: MIPDNACase | RarediseaseCase | ExistingCase, store: Store):
    if isinstance(case, ExistingCase):
        db_case: DbCase = store.get_case_by_internal_id_strict(case.internal_id)
        contains_one_sample = bool(len(db_case.samples) == 1)
    else:
        contains_one_sample = bool(len(case.samples) == 1)
    return contains_one_sample


def is_sample_related_in_case(
    sample: MIPDNASample | RarediseaseSample | ExistingSample,
    case: MIPDNACase | RarediseaseCase,
    store: Store,
):
    if not (sample.mother or sample.father):
        sample_name = get_sample_name(sample=sample, store=store)
        if all((sample_name not in [sample.mother, sample.father] for sample in case.samples)):
            return False
    return True


def get_sample_name(sample: MIPDNASample | RarediseaseSample | ExistingSample, store: Store) -> str:
    if isinstance(sample, ExistingSample):
        sample_name = store.get_sample_by_internal_id_strict(sample.internal_id).name
    else:
        sample_name = sample.name
    return sample_name
