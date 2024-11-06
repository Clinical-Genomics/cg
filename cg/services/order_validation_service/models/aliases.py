from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample

SampleWithRelatives = TomteSample | MipDnaSample
CaseContainingRelatives = TomteCase | MipDnaCase

NonHumanSample = MutantSample | MicrosaltSample
