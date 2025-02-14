from cg.services.orders.validation.workflows.mip_dna.models.case import MIPDNACase
from cg.services.orders.validation.workflows.tomte.models.case import TomteCase

CaseContainingRelatives = TomteCase | MIPDNACase

CaseWithSkipRC = TomteCase | MIPDNACase
