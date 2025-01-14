from cg.services.order_validation_service.workflows.fluffy.models.order import FluffyOrder
from cg.services.order_validation_service.workflows.metagenome.models.sample import MetagenomeSample
from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.order_validation_service.workflows.taxprofiler.models.sample import (
    TaxprofilerSample,
)

OrderWithIndexedSamples = FluffyOrder | RmlOrder
OrderWithSamplesFromOrganism = MutantOrder | MicrosaltOrder
OrderWithControlSamples = (
    MetagenomeSample | MicrobialFastqOrder | MicrosaltOrder | MutantOrder | TaxprofilerSample
)
