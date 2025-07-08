from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase
from cg.services.orders.validation.order_types.raredisease.models.case import RarediseaseCase
from cg.services.orders.validation.order_types.tomte.models.case import TomteCase

CaseContainingRelatives = MIPDNACase | RarediseaseCase | TomteCase

CaseWithSkipRC = MIPDNACase | RarediseaseCase | TomteCase
