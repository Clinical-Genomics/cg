from cg.services.order_validation_service.workflows.balsamic.models.sample import BalsamicSample
from cg.services.order_validation_service.workflows.balsamic_umi.models.sample import (
    BalsamicUmiSample,
)
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample
from cg.services.order_validation_service.workflows.fluffy.models.sample import FluffySample
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.order_validation_service.workflows.mip_rna.models.sample import MipRnaSample
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample
from cg.services.order_validation_service.workflows.rml.models.sample import RmlSample
from cg.services.order_validation_service.workflows.rna_fusion.models.sample import RnaFusionSample
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample

HumanSample = (
    BalsamicSample | BalsamicUmiSample | FastqSample | MipDnaSample | RnaFusionSample | TomteSample
)
NonHumanSample = MutantSample | MicrosaltSample

IndexedSample = FluffySample | RmlSample

SampleInCase = (
    BalsamicSample | BalsamicUmiSample | MipDnaSample | MipRnaSample | RnaFusionSample | TomteSample
)

SampleWithRelatives = TomteSample | MipDnaSample

SampleWithSkipRC = TomteSample | MipDnaSample | FastqSample
