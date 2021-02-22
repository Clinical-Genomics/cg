from typing import Optional

from cg.constants import Pipeline
from cg.meta.workflow.mip import MipAnalysisAPI


class MipRNAAnalysisAPI(MipAnalysisAPI):
    def __init__(self, config: dict, pipeline: Pipeline = Pipeline.MIP_RNA):
        super().__init__(config, pipeline)
        self.script = config["mip-rd-rna"]["script"]
        self.pipeline = config["mip-rd-rna"]["pipeline"]
        self.conda_env = config["mip-rd-rna"]["conda_env"]
        self.root = config["mip-rd-rna"]["root"]

    def config_sample(self, link_obj, panel_bed: Optional[str] = None) -> dict:
        sample_data = self.get_sample_data(link_obj)
        if link_obj.mother:
            sample_data["mother"] = link_obj.mother.internal_id
        if link_obj.father:
            sample_data["father"] = link_obj.father.internal_id
        return sample_data
