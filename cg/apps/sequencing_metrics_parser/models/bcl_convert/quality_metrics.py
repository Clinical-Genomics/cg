from pydantic import BaseModel


class BaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class BclConvertQualityMetrics(BaseModel):
    def __init__(
        self,
        lane: int,
        sample_internal_id: str,
        read_pair_number: int,
        yield_bases: int,
        yield_q30_bases: int,
        quality_score_sum: int,
        mean_quality_score_q30: float,
        percent_q30: float,
    ):
        self.lane = lane
        self.sample_internal_id = sample_internal_id
        self.read_pair_number = read_pair_number
        self.yield_bases = yield_bases
        self.yield_q30_bases = yield_q30_bases
        self.quality_score_sum = quality_score_sum
        self.mean_quality_score_q30 = mean_quality_score_q30
        self.percent_q30 = percent_q30
