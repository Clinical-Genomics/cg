import logging
from typing import List

LOG = logging.getLogger(__name__)
SEX_MAP = {"male": "M", "female": "F"}


class LimsHandler:
    @staticmethod
    def to_lims(customer: str, samples: List[dict]) -> List[dict]:
        """Convert order input to lims interface input."""
        samples_lims = []
        for sample in samples:
            LOG.debug(f"{sample['name']}: prepare LIMS input")
            samples_lims.append(
                {
                    "name": sample["name"],
                    "container": sample.get("container") or "Tube",
                    "container_name": sample.get("container_name"),
                    "well_position": sample.get("well_position"),
                    "index_sequence": sample.get("index_sequence"),
                    "udfs": {
                        "application": sample["application"],
                        "capture_kit": sample.get("capture_kit"),
                        "comment": sample.get("comment"),
                        "concentration": sample.get("concentration"),
                        "concentration_weight": sample.get("concentration_weight"),
                        "customer": customer,
                        "data_analysis": sample.get("data_analysis"),
                        "elution_buffer": sample.get("elution_buffer"),
                        "extraction_method": sample.get("extraction_method"),
                        "family_name": sample.get("family_name") or "NA",
                        "formalin_fixation_time": sample.get("formalin_fixation_time"),
                        "index": sample.get("index"),
                        "index_number": sample.get("index_number"),
                        "organism": sample.get("organism"),
                        "organism_other": sample.get("organism_other"),
                        "pool": sample.get("pool"),
                        "post_formalin_fixation_time": sample.get("post_formalin_fixation_time"),
                        "priority": sample.get("priority") or "standard",
                        "quantity": sample.get("quantity"),
                        "reference_genome": sample.get("reference_genome"),
                        "require_qcok": sample.get("require_qcok") or False,
                        "rml_plate_name": sample.get("rml_plate_name"),
                        "sex": SEX_MAP.get(sample.get("sex"), "unknown"),
                        "source": sample.get("source") or "NA",
                        "tissue_block_size": sample.get("tissue_block_size"),
                        "tumour": sample.get("tumour") or False,
                        "tumour_purity": sample.get("tumour_purity"),
                        "volume": sample.get("volume"),
                        "well_position_rml": sample.get("well_position_rml"),
                        "verified_organism": sample.get("verified_organism"),
                    },
                }
            )
        return samples_lims

    def process_lims(self, data: dict, samples: List[dict]):
        """Process samples to add them to LIMS."""
        samples_lims = self.to_lims(data["customer"], samples)
        project_name = data["ticket"] or data["name"]
        project_data = self.lims.submit_project(project_name, samples_lims)
        lims_map = self.lims.get_samples(projectlimsid=project_data["id"], map_ids=True)
        return project_data, lims_map
