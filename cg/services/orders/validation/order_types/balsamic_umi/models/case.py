from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.order_types.balsamic_umi.models.sample import BalsamicUmiSample


class BalsamicUmiCase(Case[BalsamicUmiSample]):
    cohorts: list[str] | None = None
    synopsis: str | None = None
