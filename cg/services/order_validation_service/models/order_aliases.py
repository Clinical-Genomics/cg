from cg.services.order_validation_service.workflows.fluffy.models.order import FluffyOrder
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder

OrderWithIndexedSamples = FluffyOrder | RmlOrder
OrderWithNonHumanSamples = MutantOrder | MicrosaltOrder
