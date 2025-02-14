from cg.services.orders.validation.workflows.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.workflows.metagenome.models.sample import MetagenomeSample
from cg.services.orders.validation.workflows.microbial_fastq.models.order import MicrobialFastqOrder
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.workflows.mutant.models.order import MutantOrder
from cg.services.orders.validation.workflows.rml.models.order import RMLOrder
from cg.services.orders.validation.workflows.taxprofiler.models.sample import TaxprofilerSample

OrderWithIndexedSamples = FluffyOrder | RMLOrder
OrderWithControlSamples = (
    MetagenomeSample | MicrobialFastqOrder | MicrosaltOrder | MutantOrder | TaxprofilerSample
)
