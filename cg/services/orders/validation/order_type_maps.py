from pydantic import BaseModel, ConfigDict

from cg.models.orders.constants import OrderType
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.workflows.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.workflows.balsamic.validation_rules import (
    BALSAMIC_CASE_RULES,
    BALSAMIC_CASE_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.balsamic_umi.models.order import BalsamicUmiOrder
from cg.services.orders.validation.workflows.balsamic_umi.validation_rules import (
    BALSAMIC_UMI_CASE_RULES,
    BALSAMIC_UMI_CASE_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.fastq.models.order import FastqOrder
from cg.services.orders.validation.workflows.fastq.validation_rules import FASTQ_SAMPLE_RULES
from cg.services.orders.validation.workflows.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.workflows.fluffy.validation_rules import FLUFFY_SAMPLE_RULES
from cg.services.orders.validation.workflows.metagenome.models.order import MetagenomeOrder
from cg.services.orders.validation.workflows.metagenome.validation_rules import (
    METAGENOME_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.microbial_fastq.models.order import MicrobialFastqOrder
from cg.services.orders.validation.workflows.microbial_fastq.validation_rules import (
    MICROBIAL_FASTQ_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.workflows.microsalt.validation_rules import (
    MICROSALT_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.orders.validation.workflows.mip_dna.validation_rules import (
    MIP_DNA_CASE_RULES,
    MIP_DNA_CASE_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.mip_rna.models.order import MipRnaOrder
from cg.services.orders.validation.workflows.mip_rna.validation_rules import (
    MIP_RNA_CASE_RULES,
    MIP_RNA_CASE_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.mutant.models.order import MutantOrder
from cg.services.orders.validation.workflows.mutant.validation_rules import MUTANT_SAMPLE_RULES
from cg.services.orders.validation.workflows.order_validation_rules import ORDER_RULES
from cg.services.orders.validation.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.validation.workflows.pacbio_long_read.validation_rules import (
    PACBIO_LONG_READ_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.rml.models.order import RmlOrder
from cg.services.orders.validation.workflows.rml.validation_rules import RML_SAMPLE_RULES
from cg.services.orders.validation.workflows.rna_fusion.models.order import RnaFusionOrder
from cg.services.orders.validation.workflows.rna_fusion.validation_rules import (
    RNAFUSION_CASE_RULES,
    RNAFUSION_CASE_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.taxprofiler.models.order import TaxprofilerOrder
from cg.services.orders.validation.workflows.taxprofiler.validation_rules import (
    TAXPROFILER_SAMPLE_RULES,
)
from cg.services.orders.validation.workflows.tomte.models.order import TomteOrder
from cg.services.orders.validation.workflows.tomte.validation_rules import (
    TOMTE_CASE_RULES,
    TOMTE_CASE_SAMPLE_RULES,
)


class RuleSet(BaseModel):
    case_rules: list[callable] = []
    case_sample_rules: list[callable] = []
    order_rules: list[callable] = ORDER_RULES
    sample_rules: list[callable] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


ORDER_TYPE_RULE_SET_MAP: dict[OrderType, RuleSet] = {
    OrderType.BALSAMIC: RuleSet(
        case_rules=BALSAMIC_CASE_RULES, case_sample_rules=BALSAMIC_CASE_SAMPLE_RULES
    ),
    OrderType.BALSAMIC_UMI: RuleSet(
        case_rules=BALSAMIC_UMI_CASE_RULES,
        case_sample_rules=BALSAMIC_UMI_CASE_SAMPLE_RULES,
    ),
    OrderType.FASTQ: RuleSet(
        sample_rules=FASTQ_SAMPLE_RULES,
    ),
    OrderType.FLUFFY: RuleSet(
        sample_rules=FLUFFY_SAMPLE_RULES,
    ),
    OrderType.METAGENOME: RuleSet(
        sample_rules=METAGENOME_SAMPLE_RULES,
    ),
    OrderType.MICROBIAL_FASTQ: RuleSet(
        sample_rules=MICROBIAL_FASTQ_SAMPLE_RULES,
    ),
    OrderType.MICROSALT: RuleSet(
        sample_rules=MICROSALT_SAMPLE_RULES,
    ),
    OrderType.MIP_DNA: RuleSet(
        case_rules=MIP_DNA_CASE_RULES, case_sample_rules=MIP_DNA_CASE_SAMPLE_RULES
    ),
    OrderType.MIP_RNA: RuleSet(
        case_rules=MIP_RNA_CASE_RULES,
        case_sample_rules=MIP_RNA_CASE_SAMPLE_RULES,
    ),
    OrderType.PACBIO_LONG_READ: RuleSet(
        sample_rules=PACBIO_LONG_READ_SAMPLE_RULES,
    ),
    OrderType.RML: RuleSet(
        sample_rules=RML_SAMPLE_RULES,
    ),
    OrderType.RNAFUSION: RuleSet(
        case_rules=RNAFUSION_CASE_RULES,
        case_sample_rules=RNAFUSION_CASE_SAMPLE_RULES,
    ),
    OrderType.SARS_COV_2: RuleSet(
        sample_rules=MUTANT_SAMPLE_RULES,
    ),
    OrderType.TAXPROFILER: RuleSet(
        sample_rules=TAXPROFILER_SAMPLE_RULES,
    ),
    OrderType.TOMTE: RuleSet(
        case_rules=TOMTE_CASE_RULES,
        case_sample_rules=TOMTE_CASE_SAMPLE_RULES,
    ),
}

ORDER_TYPE_MODEL_MAP: dict[OrderType, type[Order]] = {
    OrderType.BALSAMIC: BalsamicOrder,
    OrderType.BALSAMIC_UMI: BalsamicUmiOrder,
    OrderType.FASTQ: FastqOrder,
    OrderType.FLUFFY: FluffyOrder,
    OrderType.METAGENOME: MetagenomeOrder,
    OrderType.MICROBIAL_FASTQ: MicrobialFastqOrder,
    OrderType.MICROSALT: MicrosaltOrder,
    OrderType.MIP_DNA: MipDnaOrder,
    OrderType.MIP_RNA: MipRnaOrder,
    OrderType.PACBIO_LONG_READ: PacbioOrder,
    OrderType.RML: RmlOrder,
    OrderType.RNAFUSION: RnaFusionOrder,
    OrderType.SARS_COV_2: MutantOrder,
    OrderType.TAXPROFILER: TaxprofilerOrder,
    OrderType.TOMTE: TomteOrder,
}
