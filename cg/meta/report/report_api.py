"""Module to create delivery reports."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from housekeeper.store.models import File, Version
from jinja2 import Environment, PackageLoader, Template, select_autoescape
from sqlalchemy.orm import Query

from cg.constants import Pipeline
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE, FileFormat
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.exc import DeliveryReportError
from cg.io.controller import WriteStream
from cg.meta.meta import MetaAPI
from cg.meta.report.field_validators import get_empty_report_data, get_missing_report_data
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.analysis import AnalysisModel
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import SampleMetadataModel
from cg.models.report.report import (
    CaseModel,
    CustomerModel,
    DataAnalysisModel,
    ReportModel,
    ScoutReportFiles,
)
from cg.models.report.sample import ApplicationModel, MethodsModel, SampleModel, TimestampModel
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    Family,
    FamilySample,
    Sample,
)

LOG = logging.getLogger(__name__)


class ReportAPI(MetaAPI):
    """Common Delivery Report API."""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api: AnalysisAPI = analysis_api

    def create_delivery_report(
        self, case_id: str, analysis_date: datetime, force_report: bool
    ) -> str:
        """Generates the html contents of a delivery report."""
        report_data: ReportModel = self.get_report_data(
            case_id=case_id, analysis_date=analysis_date
        )
        report_data: ReportModel = self.validate_report_fields(
            case_id=case_id, report_data=report_data, force_report=force_report
        )
        rendered_report: str = self.render_delivery_report(report_data=report_data.model_dump())
        return rendered_report

    def create_delivery_report_file(
        self, case_id: str, directory: Path, analysis_date: datetime, force_report: bool
    ) -> Path:
        """Generates a file containing the delivery report content."""
        directory.mkdir(parents=True, exist_ok=True)
        delivery_report: str = self.create_delivery_report(
            case_id=case_id, analysis_date=analysis_date, force_report=force_report
        )
        report_file_path: Path = Path(directory, "delivery-report.html")
        with open(report_file_path, "w") as delivery_report_stream:
            delivery_report_stream.write(delivery_report)
        return report_file_path

    def add_delivery_report_to_hk(
        self, case_id: str, delivery_report_file: Path, version: Version
    ) -> Optional[File]:
        """Add a delivery report file to a case bundle and return its file object."""
        LOG.info(f"Adding a new delivery report to housekeeper for {case_id}")
        file: File = self.housekeeper_api.add_file(
            path=delivery_report_file, version_obj=version, tags=[case_id, HK_DELIVERY_REPORT_TAG]
        )
        self.housekeeper_api.include_file(file, version)
        self.housekeeper_api.add_commit(file)
        return file

    def get_delivery_report_from_hk(self, case_id: str, version: Version) -> Optional[str]:
        """Return path of a delivery report stored in HK."""
        delivery_report: File = self.housekeeper_api.get_latest_file(
            bundle=case_id, tags=[HK_DELIVERY_REPORT_TAG], version=version.id
        )
        if not delivery_report:
            LOG.warning(f"No delivery report found in housekeeper for {case_id}")
            return None
        return delivery_report.full_path

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """Return the file path of the uploaded to Scout file given its tag."""
        raise NotImplementedError

    def render_delivery_report(self, report_data: dict) -> str:
        """Renders the report on the Jinja template."""
        env: Environment = Environment(
            loader=PackageLoader("cg", "meta/report/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template: Template = env.get_template(self.get_template_name())
        return template.render(**report_data)

    def get_cases_without_delivery_report(self, pipeline: Pipeline) -> list[Family]:
        """Returns a list of cases that has been stored and need a delivery report."""
        stored_cases: list[Family] = []
        analyses: Query = self.status_db.analyses_to_delivery_report(pipeline=pipeline)[
            :MAX_ITEMS_TO_RETRIEVE
        ]
        for analysis_obj in analyses:
            case: Family = analysis_obj.family
            last_version: Version = self.housekeeper_api.last_version(bundle=case.internal_id)
            hk_file: File = self.housekeeper_api.get_files(
                bundle=case.internal_id, version=last_version.id if last_version else None
            ).first()

            if hk_file and Path(hk_file.full_path).is_file():
                stored_cases.append(case)
            else:
                LOG.warning(
                    f"Case {case.internal_id} must be stored before creating a delivery report"
                )
        return stored_cases

    def get_cases_without_uploaded_delivery_report(self, pipeline: Pipeline) -> list[Family]:
        """Returns a list of cases that need a delivery report to be uploaded."""
        analyses: Query = self.status_db.analyses_to_upload_delivery_reports(pipeline=pipeline)[
            :MAX_ITEMS_TO_RETRIEVE
        ]
        return [analysis_obj.family for analysis_obj in analyses]

    def update_delivery_report_date(self, case: Family, analysis_date: datetime) -> None:
        """Updates the date when delivery report was created."""
        analysis: Analysis = self.status_db.get_analysis_by_case_entry_id_and_started_at(
            case_entry_id=case.id, started_at_date=analysis_date
        )
        analysis.delivery_report_created_at = datetime.now()
        self.status_db.session.commit()

    def get_report_data(self, case_id: str, analysis_date: datetime) -> ReportModel:
        """Fetches all the data needed to generate a delivery report."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis: Analysis = self.status_db.get_analysis_by_case_entry_id_and_started_at(
            case_entry_id=case.id, started_at_date=analysis_date
        )
        analysis_metadata: AnalysisModel = self.analysis_api.get_latest_metadata(case.internal_id)
        case_model: CaseModel = self.get_case_data(case, analysis, analysis_metadata)
        return ReportModel(
            customer=self.get_customer_data(case=case),
            version=self.get_report_version(analysis=analysis),
            date=datetime.today(),
            case=case_model,
            accredited=self.get_report_accreditation(
                samples=case_model.samples, analysis_metadata=analysis_metadata
            ),
        )

    def validate_report_fields(
        self, case_id: str, report_data: ReportModel, force_report
    ) -> ReportModel:
        """Verifies that the required report fields are not empty."""
        required_fields: dict = self.get_required_fields(case=report_data.case)
        empty_report_fields: dict = get_empty_report_data(report_data=report_data)
        missing_report_fields: dict = get_missing_report_data(
            empty_fields=empty_report_fields, required_fields=required_fields
        )
        if missing_report_fields and not force_report:
            LOG.error(
                f"Could not generate report data for {case_id}. "
                f"Missing data: \n{WriteStream.write_stream_from_content(content=missing_report_fields, file_format=FileFormat.YAML)}"
            )
            raise DeliveryReportError
        if empty_report_fields:
            LOG.warning(
                f"Empty report fields: \n{WriteStream.write_stream_from_content(content=empty_report_fields, file_format=FileFormat.YAML)}"
            )
        return report_data

    @staticmethod
    def get_customer_data(case: Family) -> CustomerModel:
        """Returns customer validated attributes retrieved from status DB."""
        return CustomerModel(
            name=case.customer.name,
            id=case.customer.internal_id,
            invoice_address=case.customer.invoice_address,
            scout_access=case.customer.scout_access,
        )

    @staticmethod
    def get_report_version(analysis: Analysis) -> int:
        """
        Returns the version of the given analysis. The version of the first analysis is 1 and subsequent reruns
        increase it by 1.
        """
        version = None
        if analysis:
            version = len(analysis.family.analyses) - analysis.family.analyses.index(analysis)
        return version

    def get_case_data(
        self,
        case: Family,
        analysis: Analysis,
        analysis_metadata: AnalysisModel,
    ) -> CaseModel:
        """Returns case associated validated attributes."""
        samples: list[SampleModel] = self.get_samples_data(
            case=case, analysis_metadata=analysis_metadata
        )
        unique_applications: list[ApplicationModel] = self.get_unique_applications(samples=samples)
        return CaseModel(
            name=case.name,
            id=case.internal_id,
            data_analysis=self.get_case_analysis_data(
                case=case, analysis=analysis, analysis_metadata=analysis_metadata
            ),
            samples=samples,
            applications=unique_applications,
        )

    def get_samples_data(self, case: Family, analysis_metadata: AnalysisModel) -> list[SampleModel]:
        """Extracts all the samples associated to a specific case and their attributes."""
        samples = list()
        case_samples: list[FamilySample] = self.status_db.get_case_samples_by_case_id(
            case_internal_id=case.internal_id
        )
        for case_sample in case_samples:
            sample: Sample = case_sample.sample
            lims_sample: Optional[dict] = self.get_lims_sample(sample_id=sample.internal_id)
            samples.append(
                SampleModel(
                    name=sample.name,
                    id=sample.internal_id,
                    ticket=sample.original_ticket,
                    gender=sample.sex,
                    source=lims_sample.get("source") if lims_sample else None,
                    tumour=sample.is_tumour,
                    application=self.get_sample_application_data(lims_sample=lims_sample),
                    methods=self.get_sample_methods_data(sample_id=sample.internal_id),
                    status=case_sample.status,
                    metadata=self.get_sample_metadata(
                        case=case, sample=sample, analysis_metadata=analysis_metadata
                    ),
                    timestamps=self.get_sample_timestamp_data(sample=sample),
                )
            )
        return samples

    def get_lims_sample(self, sample_id: str) -> Optional[dict]:
        """Fetches sample data from LIMS. Returns an empty dictionary if the request was unsuccessful."""
        lims_sample = dict()
        try:
            lims_sample: dict = self.lims_api.sample(sample_id)
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)
        return lims_sample

    def get_pipeline_accreditation_limitation(self, application_tag: str) -> str | None:
        """Return pipeline specific limitations given an application tag."""
        application_limitation: ApplicationLimitations = (
            self.status_db.get_application_limitation_by_tag_and_pipeline(
                tag=application_tag, pipeline=self.analysis_api.pipeline
            )
        )
        return application_limitation.limitations if application_limitation else None

    def get_sample_application_data(self, lims_sample: dict) -> ApplicationModel:
        """Retrieves the analysis application attributes."""
        application: Application = self.status_db.get_application_by_tag(
            tag=lims_sample.get("application")
        )
        return (
            ApplicationModel(
                tag=application.tag,
                version=lims_sample.get("application_version"),
                prep_category=application.prep_category,
                description=application.description,
                details=application.details,
                limitations=application.limitations,
                pipeline_limitations=self.get_pipeline_accreditation_limitation(application.tag),
                accredited=application.is_accredited,
                external=application.is_external,
            )
            if application
            else ApplicationModel()
        )

    @staticmethod
    def get_unique_applications(samples: list[SampleModel]) -> list[ApplicationModel]:
        """Returns the unique case associated applications."""
        applications = list()
        for sample in samples:
            if sample.application not in applications:
                applications.append(sample.application)
        return applications

    def get_sample_methods_data(self, sample_id: str) -> MethodsModel:
        """Fetches sample library preparation and sequencing methods from LIMS."""
        library_prep = None
        sequencing = None
        try:
            library_prep = self.lims_api.get_prep_method(lims_id=sample_id)
            sequencing = self.lims_api.get_sequencing_method(lims_id=sample_id)
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample (%s) methods from LIMS: %s", sample_id, ex)

        return MethodsModel(library_prep=library_prep, sequencing=sequencing)

    def get_case_analysis_data(
        self,
        case: Family,
        analysis: Analysis,
        analysis_metadata: AnalysisModel,
    ) -> DataAnalysisModel:
        """Retrieves the pipeline attributes used for data analysis."""
        return DataAnalysisModel(
            customer_pipeline=case.data_analysis,
            data_delivery=case.data_delivery,
            pipeline=analysis.pipeline,
            pipeline_version=analysis.pipeline_version,
            type=self.get_data_analysis_type(case=case),
            genome_build=self.get_genome_build(analysis_metadata=analysis_metadata),
            variant_callers=self.get_variant_callers(_analysis_metadata=analysis_metadata),
            panels=case.panels,
            scout_files=self.get_scout_uploaded_files(case=case),
        )

    def get_scout_uploaded_files(self, case: Family) -> ScoutReportFiles:
        """Extracts the files that will be uploaded to Scout."""
        return ScoutReportFiles(
            snv_vcf=self.get_scout_uploaded_file_from_hk(
                case_id=case.internal_id, scout_tag="snv_vcf"
            ),
            sv_vcf=self.get_scout_uploaded_file_from_hk(
                case_id=case.internal_id, scout_tag="sv_vcf"
            ),
            vcf_str=self.get_scout_uploaded_file_from_hk(
                case_id=case.internal_id, scout_tag="vcf_str"
            ),
            smn_tsv=self.get_scout_uploaded_file_from_hk(
                case_id=case.internal_id, scout_tag="smn_tsv"
            ),
        )

    @staticmethod
    def get_sample_timestamp_data(sample: Sample) -> TimestampModel:
        """Retrieves the sample processing dates."""
        return TimestampModel(
            ordered_at=sample.ordered_at,
            received_at=sample.received_at,
            prepared_at=sample.prepared_at,
            reads_updated_at=sample.reads_updated_at,
        )

    def get_sample_metadata(
        self,
        case: Family,
        sample: Sample,
        analysis_metadata: AnalysisModel,
    ) -> SampleMetadataModel:
        """Return the sample metadata to include in the report."""
        raise NotImplementedError

    def get_data_analysis_type(self, case: Family) -> Optional[str]:
        """Retrieves the data analysis type carried out."""
        case_sample: Sample = self.status_db.get_case_samples_by_case_id(
            case_internal_id=case.internal_id
        )[0].sample
        lims_sample: Optional[dict] = self.get_lims_sample(sample_id=case_sample.internal_id)
        application: Application = self.status_db.get_application_by_tag(
            tag=lims_sample.get("application")
        )
        return application.analysis_type if application else None

    def get_genome_build(self, analysis_metadata: AnalysisModel) -> str:
        """Returns the build version of the genome reference of a specific case."""
        raise NotImplementedError

    def get_variant_callers(self, _analysis_metadata: AnalysisModel) -> list:
        """Extracts the list of variant-calling filters used during analysis."""
        return []

    def get_report_accreditation(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Checks if the report is accredited or not."""
        raise NotImplementedError

    def get_required_fields(self, case: CaseModel) -> dict:
        """Retrieves a dictionary with the delivery report required fields."""
        raise NotImplementedError

    def get_template_name(self) -> str:
        """Retrieves the pipeline specific template name."""
        raise NotImplementedError

    @staticmethod
    def get_application_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Retrieves sample required fields."""
        required_sample_fields = dict()
        for application in case.applications:
            required_sample_fields.update({application.tag: required_fields})
        return required_sample_fields

    @staticmethod
    def get_sample_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Retrieves sample required fields."""
        required_sample_fields = dict()
        for sample in case.samples:
            required_sample_fields.update({sample.id: required_fields})
        return required_sample_fields

    @staticmethod
    def get_timestamp_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Retrieves sample timestamps required fields."""
        for sample in case.samples:
            if sample.application.external:
                required_fields.remove("received_at")
                break
        return ReportAPI.get_sample_required_fields(case=case, required_fields=required_fields)

    def get_hk_scout_file_tags(self, scout_tag: str) -> Optional[list]:
        """Retrieves pipeline specific uploaded to Scout Housekeeper file tags given a Scout key."""
        tags = self.get_upload_case_tags().get(scout_tag)
        return list(tags) if tags else None

    def get_upload_case_tags(self):
        """Retrieves pipeline specific upload case tags."""
        raise NotImplementedError
