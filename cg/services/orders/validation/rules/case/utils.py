from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.workflows.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.workflows.balsamic_umi.models.case import BalsamicUmiCase
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


def is_case_not_from_collaboration(case: ExistingCase, customer_id: str, store: Store) -> bool:
    db_case: DbCase | None = store.get_case_by_internal_id(case.internal_id)
    customer: Customer | None = store.get_customer_by_internal_id(customer_id)
    return db_case and customer and db_case.customer not in customer.collaborators
