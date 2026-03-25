from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.order_types.mip_rna.models.sample import MIPRNASample


class MIPRNACase(Case[MIPRNASample]):
    cohorts: list[str] | None = None
    synopsis: str | None = None
