from cg.services.orders.validation.workflows.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.workflows.balsamic_umi.models.sample import BalsamicUmiSample
from cg.services.orders.validation.workflows.fastq.models.sample import FastqSample
from cg.services.orders.validation.workflows.fluffy.models.sample import FluffySample
from cg.services.orders.validation.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.orders.validation.workflows.mip_rna.models.sample import MipRnaSample
from cg.services.orders.validation.workflows.rml.models.sample import RmlSample
from cg.services.orders.validation.workflows.rna_fusion.models.sample import RnaFusionSample
from cg.services.orders.validation.workflows.tomte.models.sample import TomteSample

HumanSample = (
    BalsamicSample | BalsamicUmiSample | FastqSample | MipDnaSample | RnaFusionSample | TomteSample
)

IndexedSample = FluffySample | RmlSample

SampleInCase = (
    BalsamicSample | BalsamicUmiSample | MipDnaSample | MipRnaSample | RnaFusionSample | TomteSample
)

SampleWithRelatives = TomteSample | MipDnaSample

SampleWithSkipRC = TomteSample | MipDnaSample | FastqSample
