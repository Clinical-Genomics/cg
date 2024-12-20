from cg.services.order_validation_service.workflows.balsamic.models.sample import BalsamicSample
from cg.services.order_validation_service.workflows.balsamic_umi.models.sample import (
    BalsamicUmiSample,
)
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample
from cg.services.order_validation_service.workflows.fluffy.models.order import FluffyOrder
from cg.services.order_validation_service.workflows.fluffy.models.sample import FluffySample
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.order_validation_service.workflows.mip_rna.models.sample import MipRnaSample
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.order_validation_service.workflows.rml.models.sample import RmlSample
from cg.services.order_validation_service.workflows.rna_fusion.models.sample import RnaFusionSample
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample

SampleWithRelatives = TomteSample | MipDnaSample


NonHumanSample = MutantSample | MicrosaltSample
HumanSample = (
    BalsamicSample | BalsamicUmiSample | FastqSample | MipDnaSample | RnaFusionSample | TomteSample
)

SampleInCase = (
    BalsamicSample | BalsamicUmiSample | MipDnaSample | MipRnaSample | RnaFusionSample | TomteSample
)


SampleWithSkipRC = TomteSample | MipDnaSample | FastqSample

IndexedSample = FluffySample | RmlSample
OrderWithIndexedSamples = RmlOrder | FluffyOrder
