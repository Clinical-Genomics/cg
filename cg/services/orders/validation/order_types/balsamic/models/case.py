from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample


class BalsamicCase(Case[BalsamicSample]):
    cohorts: list[str] | None = None
    synopsis: str | None = None
