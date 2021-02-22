from typing import Optional

from cg.constants import Pipeline, DEFAULT_CAPTURE_KIT
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import models


class MipDNAAnalysisAPI(MipAnalysisAPI):
    def __init__(self, config: dict, pipeline: Pipeline = Pipeline.MIP_DNA):
        super().__init__(config, pipeline)
        self.script = config["mip-rd-dna"]["script"]
        self.pipeline = config["mip-rd-dna"]["pipeline"]
        self.conda_env = config["mip-rd-dna"]["conda_env"]
        self.root = config["mip-rd-dna"]["root"]

    def config_sample(self, link_obj: models.FamilySample, panel_bed: Optional[str]) -> dict:
        sample_data = self.get_sample_data(link_obj)
        if sample_data["analysis_type"] == "wgs":
            sample_data["capture_kit"] = panel_bed or DEFAULT_CAPTURE_KIT
        else:
            sample_data["capture_kit"] = panel_bed or self.get_target_bed_from_lims(
                link_obj.sample.internal_id
            )
        if link_obj.mother:
            sample_data["mother"] = link_obj.mother.internal_id
        if link_obj.father:
            sample_data["father"] = link_obj.father.internal_id
        return sample_data
