from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample


class RNAFusionCase(Case[RNAFusionSample]):
    cohorts: list[str] | None = None
    synopsis: str | None = None
