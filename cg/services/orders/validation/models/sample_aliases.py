from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.order_types.balsamic_umi.models.sample import BalsamicUmiSample
from cg.services.orders.validation.order_types.fastq.models.sample import FastqSample
from cg.services.orders.validation.order_types.fluffy.models.sample import FluffySample
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample
from cg.services.orders.validation.order_types.mip_rna.models.sample import MIPRNASample
from cg.services.orders.validation.order_types.rml.models.sample import RMLSample
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample
from cg.services.orders.validation.order_types.tomte.models.sample import TomteSample

HumanSample = (
    BalsamicSample | BalsamicUmiSample | FastqSample | MIPDNASample | RNAFusionSample | TomteSample
)

IndexedSample = FluffySample | RMLSample

SampleInCase = (
    BalsamicSample | BalsamicUmiSample | MIPDNASample | MIPRNASample | RNAFusionSample | TomteSample
)

SampleWithRelatives = TomteSample | MIPDNASample

SampleWithSkipRC = TomteSample | MIPDNASample | FastqSample
