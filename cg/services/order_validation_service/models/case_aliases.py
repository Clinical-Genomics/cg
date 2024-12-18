from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase

CaseContainingRelatives = TomteCase | MipDnaCase

CaseWithSkipRC = TomteCase | MipDnaCase
