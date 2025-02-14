from cg.services.orders.validation.workflows.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.workflows.balsamic_umi.models.sample import BalsamicUmiSample
from cg.services.orders.validation.workflows.fastq.models.sample import FastqSample
from cg.services.orders.validation.workflows.fluffy.models.sample import FluffySample
from cg.services.orders.validation.workflows.mip_dna.models.sample import MIPDNASample
from cg.services.orders.validation.workflows.mip_rna.models.sample import MIPRNASample
from cg.services.orders.validation.workflows.rml.models.sample import RMLSample
from cg.services.orders.validation.workflows.rna_fusion.models.sample import RNAFusionSample
from cg.services.orders.validation.workflows.tomte.models.sample import TomteSample

HumanSample = (
    BalsamicSample | BalsamicUmiSample | FastqSample | MIPDNASample | RNAFusionSample | TomteSample
)

IndexedSample = FluffySample | RMLSample

SampleInCase = (
    BalsamicSample | BalsamicUmiSample | MIPDNASample | MIPRNASample | RNAFusionSample | TomteSample
)

SampleWithRelatives = TomteSample | MIPDNASample

SampleWithSkipRC = TomteSample | MIPDNASample | FastqSample
