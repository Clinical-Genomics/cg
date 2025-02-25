from cg.services.orders.validation.order_types.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.order_types.metagenome.models.sample import MetagenomeSample
from cg.services.orders.validation.order_types.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.rml.models.order import RMLOrder
from cg.services.orders.validation.order_types.taxprofiler.models.sample import TaxprofilerSample

OrderWithIndexedSamples = FluffyOrder | RMLOrder
OrderWithControlSamples = (
    MetagenomeSample | MicrobialFastqOrder | MicrosaltOrder | MutantOrder | TaxprofilerSample
)
