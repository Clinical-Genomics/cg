from typing import Optional, Any

from cgmodels.cg.constants import Pipeline
from pydantic import BaseModel, constr, conlist

from cg.models.orders.samples import (
    BaseSample,
    MipDnaSample,
    BalsamicSample,
    FastqSample,
    MetagenomeSample,
    MicrobialSample,
    MipRnaSample,
    RmlSample,
    SarsCov2Sample,
)
from cg.store import models
from cg.utils.StrEnum import StrEnum


class OrderType(StrEnum):
    BALSAMIC: str = str(Pipeline.BALSAMIC)
    FASTQ: str = str(Pipeline.FASTQ)
    FLUFFY: str = str(Pipeline.FLUFFY)
    METAGENOME: str = "metagenome"
    MICROSALT: str = str(Pipeline.MICROSALT)
    MIP_DNA: str = str(Pipeline.MIP_DNA)
    MIP_RNA: str = str(Pipeline.MIP_RNA)
    RML: str = "rml"
    SARS_COV_2: str = str(Pipeline.SARS_COV_2)


class OrderIn(BaseModel):
    name: constr(min_length=2, max_length=models.Sample.order.property.columns[0].type.length)
    comment: Optional[str]
    customer: constr(
        min_length=1, max_length=models.Customer.internal_id.property.columns[0].type.length
    )
    samples: conlist(Any, min_items=1)
    ticket: Optional[str]

    @classmethod
    def parse_obj(cls, obj: dict, project: OrderType):
        parsed_obj = super().parse_obj(obj)
        parsed_obj.parse_samples(project=project)
        return parsed_obj

    def parse_samples(self, project: OrderType):
        """
        Parses samples of by the type given by the project

        Parameters:
            project (OrderType): type of project

        Returns:
            Nothing
        """
        parsed_samples = []

        sample: dict
        for sample in self.samples:
            parsed_sample = None

            if project == OrderType.BALSAMIC:
                parsed_sample: BalsamicSample = BalsamicSample.parse_obj(sample)
            elif project == OrderType.FASTQ:
                parsed_sample: FastqSample = FastqSample.parse_obj(sample)
            elif project == OrderType.FLUFFY:
                parsed_sample: RmlSample = RmlSample.parse_obj(sample)
            elif project == OrderType.METAGENOME:
                parsed_sample: MetagenomeSample = MetagenomeSample.parse_obj(sample)
            elif project == OrderType.MICROSALT:
                parsed_sample: MicrobialSample = MicrobialSample.parse_obj(sample)
            elif project == OrderType.MIP_DNA:
                parsed_sample: MipDnaSample = MipDnaSample.parse_obj(sample)
            elif project == OrderType.MIP_RNA:
                parsed_sample: MipRnaSample = MipRnaSample.parse_obj(sample)
            elif project == OrderType.RML:
                parsed_sample: RmlSample = RmlSample.parse_obj(sample)
            elif project == OrderType.SARS_COV_2:
                parsed_sample: SarsCov2Sample = SarsCov2Sample.parse_obj(sample)
            if parsed_sample:
                parsed_samples.append(parsed_sample)

        self.samples = parsed_samples
