from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase
from cg.services.orders.validation.order_types.tomte.models.case import TomteCase

CaseContainingRelatives = TomteCase | MIPDNACase

CaseWithSkipRC = TomteCase | MIPDNACase
