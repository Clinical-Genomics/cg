"""Module to create delivery reports"""

from datetime import datetime
import logging
from pathlib import Path
from typing import TextIO, Optional, List

import housekeeper
import requests
from cg.meta.workflow.analysis import AnalysisAPI
from cg.constants.tags import HK_DELIVERY_REPORT_TAG
from cg.models.cg_config import CGConfig
from cg.meta.meta import MetaAPI
from cg.models.report.report import ReportModel, CustomerModel, CaseModel, DataAnalysisModel
from cg.models.report.sample import (
    SampleModel,
    ApplicationModel,
    TimestampModel,
    MethodsModel,
    MetadataModel,
)
from cg.store import models
from jinja2 import Environment, PackageLoader, select_autoescape

LOG = logging.getLogger(__name__)


class ReportAPI(MetaAPI):
    """Parent class of existing report APIs"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api = analysis_api

    def create_delivery_report(self, case_id: str, analysis_date: datetime) -> str:
        """Generates the html contents of a delivery report"""

        report_data = self.get_report_data(case_id=case_id, analysis_date=analysis_date)
        rendered_report = self.render_delivery_report(report_data)
        return rendered_report

    def create_delivery_report_file(
        self, case_id: str, file_path: Path, analysis_date: datetime
    ) -> TextIO:
        """Generates a temporary file containing a delivery report"""

        file_path.mkdir(parents=True, exist_ok=True)
        delivery_report = self.create_delivery_report(case_id=case_id, analysis_date=analysis_date)

        report_file_path = Path(file_path / "delivery-report.html")
        with open(report_file_path, "w") as delivery_report_file:
            delivery_report_file.write(delivery_report)

        return delivery_report_file

    def add_delivery_report_to_hk(
        self, delivery_report_file: Path, case_id: str, analysis_date: datetime
    ) -> Optional[housekeeper.store.models.File]:
        """
        Adds a delivery report file, if it has not already been generated, to an analysis bundle for a specific case
        in HK and returns a pointer to it
        """

        version = self.housekeeper_api.version(case_id, analysis_date)
        try:
            self.get_delivery_report_from_hk(case_id=case_id)
        except FileNotFoundError:
            file = self.housekeeper_api.add_file(
                delivery_report_file.name, version, HK_DELIVERY_REPORT_TAG
            )
            self.housekeeper_api.include_file(file, version)
            self.housekeeper_api.add_commit(file)
            return file

        return None

    def get_delivery_report_from_hk(self, case_id: str) -> str:
        """Extracts the delivery reports of a specific case stored in HK"""

        version = self.housekeeper_api.last_version(case_id)
        delivery_report_files = self.housekeeper_api.get_files(
            bundle=case_id, tags=[HK_DELIVERY_REPORT_TAG], version=version.id
        )

        if delivery_report_files.count() == 0:
            raise FileNotFoundError(f"No delivery report was found in housekeeper for {case_id}")

        return delivery_report_files[0].full_path

    @staticmethod
    def render_delivery_report(report_data: dict) -> str:
        """Renders the report on the Jinja template"""

        env = Environment(
            loader=PackageLoader("cg", "meta/report/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(
            f"{report_data['case']['data_analysis']['pipeline']}_report.html"
        )
        return template.render(**report_data)

    def get_cases_without_delivery_report(self):
        """Returns a list of analyses that need a delivery report"""

        return self.status_db.analyses_to_delivery_report(self.analysis_api.pipeline)[:50]

    def get_report_data(self, case_id: str, analysis_date: datetime) -> dict:
        """Fetches all the data needed to generate a delivery report"""

        case = self.status_db.family(case_id)
        analysis = self.status_db.analysis(case, analysis_date)
        case_model = self.get_case_data(case, analysis)

        return ReportModel(
            customer=self.get_customer_data(case),
            version=self.get_report_version(analysis),
            date=datetime.today(),
            case=case_model,
            accredited=self.get_report_accreditation(case_model.samples),
        ).dict()

    @staticmethod
    def get_customer_data(case: models.Family) -> CustomerModel:
        """Returns customer validated attributes retrieved from status DB"""

        return CustomerModel(
            name=case.customer.name,
            id=case.customer.internal_id,
            invoice_address=case.customer.invoice_address,
            scout_access=case.customer.scout_access,
        )

    @staticmethod
    def get_report_version(analysis: models.Analysis) -> int:
        """
        Returns the version of the given analysis. The version of the first analysis is 1 and subsequent reruns
        increase it by 1.
        """

        version = None

        if analysis:
            version = len(analysis.family.analyses) - analysis.family.analyses.index(analysis)

        return version

    @staticmethod
    def get_report_accreditation(samples: List[SampleModel]) -> bool:
        """Checks if the report is accredited or not by evaluating each of the sample process accreditations"""

        for sample in samples:
            if not sample.application.accredited:
                return False

        return True

    def get_case_data(self, case: models.Family, analysis: models.Analysis) -> CaseModel:
        """Returns case associated validated attributes"""

        return CaseModel(
            name=case.name,
            data_analysis=self.get_case_analysis_data(case, analysis),
            panels=case.panels,
            samples=self.get_samples_data(case),
        )

    def get_samples_data(self, case: models.Family) -> List[SampleModel]:
        """Extracts all the samples associated to a specific case and their attributes"""

        samples = list()
        case_samples = self.status_db.family_samples(case.internal_id)

        for case_sample in case_samples:
            sample = case_sample.sample
            lims_sample = self.get_lims_sample(sample.internal_id)

            samples.append(
                SampleModel(
                    name=lims_sample.get("name"),
                    id=sample.internal_id,
                    ticket=sample.ticket_number,
                    gender=lims_sample.get("sex"),
                    source=lims_sample.get("source"),
                    tumour=sample.is_tumour,
                    application=self.get_sample_application_data(lims_sample),
                    methods=self.get_sample_methods_data(sample.internal_id),
                    status=case_sample.status,
                    metadata=self.get_metadata(sample, case),
                    timestamp=self.get_sample_timestamp_data(sample),
                )
            )

        return samples

    def get_lims_sample(self, sample_id: str) -> dict:
        """Fetches sample data from LIMS. Returns an empty dictionary if the request was unsuccessful"""

        lims_sample = dict()
        try:
            lims_sample = self.lims_api.sample(sample_id)
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)

        return lims_sample

    def get_sample_application_data(self, lims_sample: dict) -> ApplicationModel:
        """Retrieves the analysis application attributes"""

        application = self.status_db.application(tag=lims_sample.get("application"))

        return ApplicationModel(
            tag=application.tag,
            version=lims_sample.get("application_version"),
            prep_category=application.prep_category,
            description=application.description,
            limitations=application.limitations,
            accredited=application.is_accredited,
        )

    def get_sample_methods_data(self, sample_id: str) -> MethodsModel:
        """Fetches sample library preparation and sequencing methods from LIMS"""

        library_prep = None
        sequencing = None
        try:
            library_prep = self.lims_api.get_prep_method(sample_id)
            sequencing = self.lims_api.get_sequencing_method(sample_id)
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample (%s) methods from LIMS: %s", sample_id, ex)

        return MethodsModel(library_prep=library_prep, sequencing=sequencing)

    @staticmethod
    def get_case_analysis_data(case: models.Family, analysis: models.Analysis) -> DataAnalysisModel:
        """Retrieves the pipeline attributes used for data analysis"""

        return DataAnalysisModel(
            customer_pipeline=case.data_analysis,
            pipeline=analysis.pipeline,
            pipeline_version=analysis.pipeline_version,
        )

    def get_sample_timestamp_data(self, sample: models.Sample) -> TimestampModel:
        """Retrieves the sample processing dates"""

        return TimestampModel(
            ordered_at=sample.ordered_at,
            received_at=sample.received_at,
            prepared_at=sample.prepared_at,
            sequenced_at=sample.sequenced_at,
            delivered_at=sample.delivered_at,
            processing_days=self.get_processing_dates(sample),
        )

    @staticmethod
    def get_processing_dates(sample: models.Sample) -> int:
        """Calculates the days it takes to deliver a sample"""

        if sample.received_at and sample.delivered_at:
            return (sample.delivered_at - sample.received_at).days

        return None

    def get_metadata(self, sample: models.Sample, case: models.Family) -> MetadataModel:
        """Fetches the sample metadata to include in the report"""

        raise NotImplementedError

    '''

    @staticmethod
    def update_delivery_report_date(
        status_api: Store, case_id: str, analysis_date: datetime
    ) -> None:
        """Update date on analysis when delivery report was created"""

        case_obj = status_api.family(case_id)
        analysis_obj = status_api.analysis(case_obj, analysis_date)
        analysis_obj.delivery_report_created_at = datetime.now()
        status_api.commit()


    '''
