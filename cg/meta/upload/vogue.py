"""API to run Vogue"""

import datetime as dt
from typing import Optional, List

from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI
from cg.constants.constants import FileFormat
from cg.io.controller import ReadStream
from cg.store import Store
from cg.store.models import Application, Analysis


class UploadVogueAPI:
    """API to load data into Vogue"""

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI, store: Store):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api
        self.store = store

    def load_genotype(self, days: int) -> None:
        """Loading genotype data from the genotype database into the trending database"""

        samples: dict = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.genotype_api.export_sample(days=days)
        )
        for sample_id, sample_dict in samples.items():
            sample_dict["_id"] = sample_id
            self.vogue_api.load_genotype_data(sample_dict)

        samples_analysis: dict = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.genotype_api.export_sample_analysis(days=days)
        )
        for sample_id, sample_dict in samples_analysis.items():
            sample_dict["_id"] = sample_id
            self.vogue_api.load_genotype_data(sample_dict)

    def load_apptags(self) -> None:
        """Loading application tags from statusdb into the trending database"""
        applications: List[Application] = self.store.get_applications()
        apptags_for_vogue = [
            {"tag": application.tag, "prep_category": application.prep_category}
            for application in applications
        ]

        self.vogue_api.load_apptags(apptags_for_vogue)

    def load_bioinfo_raw(self, load_bioinfo_inputs):
        """Running vogue load bioinfo raw."""

        self.vogue_api.load_bioinfo_raw(load_bioinfo_inputs)

    def load_bioinfo_process(self, load_bioinfo_inputs, cleanup):
        """Running vogue load bioinfo process."""

        self.vogue_api.load_bioinfo_process(load_bioinfo_inputs, cleanup)

    def load_bioinfo_sample(self, load_bioinfo_inputs):
        """Running vogue load bioinfo sample."""

        self.vogue_api.load_bioinfo_sample(load_bioinfo_inputs)

    @staticmethod
    def update_analysis_uploaded_to_vogue_date(
        analysis: Analysis,
        vogue_upload_date: Optional[dt.datetime] = dt.datetime.now(),
    ) -> Analysis:
        analysis.uploaded_to_vogue_at = vogue_upload_date
        return analysis
