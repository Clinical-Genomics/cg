from cg.services.orders.validation.workflows.mip_dna.models.case import MipDnaCase
from cg.services.orders.validation.workflows.tomte.models.case import TomteCase

CaseContainingRelatives = TomteCase | MipDnaCase

CaseWithSkipRC = TomteCase | MipDnaCase
