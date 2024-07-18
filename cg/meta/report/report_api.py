"""Module to create delivery reports."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from housekeeper.store.models import File, Version
from jinja2 import Environment, PackageLoader, Template, select_autoescape
from sqlalchemy.orm import Query

from cg.constants import DELIVERY_REPORT_FILE_NAME, SWEDAC_LOGO_PATH, Workflow
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE, FileFormat
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG, HermesFileTag
from cg.exc import DeliveryReportError
from cg.io.controller import ReadFile, WriteStream
from cg.meta.meta import MetaAPI
from cg.meta.report.field_validators import (
    get_empty_report_data,
    get_missing_report_data,
)
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
from cg.models.report.sample import (
    ApplicationModel,
    MethodsModel,
    SampleModel,
    TimestampModel,
)
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    Case,
    CaseSample,
    Sample,
)

LOG = logging.getLogger(__name__)


class ReportAPI(MetaAPI):
    """Common Delivery Report API."""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api: AnalysisAPI = analysis_api

    def create_delivery_report(self, case_id: str, analysis_date: datetime, force: bool) -> str:
        """Generates the HTML content of a delivery report."""
        report_data: ReportModel = self.get_report_data(
            case_id=case_id, analysis_date=analysis_date
        )
        report_data: ReportModel = self.validate_report_fields(
            case_id=case_id, report_data=report_data, force=force
        )
        rendered_report: str = self.render_delivery_report(report_data=report_data.model_dump())
        return rendered_report

    def create_delivery_report_file(
        self, case_id: str, directory: Path, analysis_date: datetime, force: bool
    ) -> Path:
        """Generates a file containing the delivery report content."""
        directory.mkdir(parents=True, exist_ok=True)
        delivery_report: str = self.create_delivery_report(
            case_id=case_id, analysis_date=analysis_date, force=force
        )
        report_file_path: Path = Path(directory, DELIVERY_REPORT_FILE_NAME)
        with open(report_file_path, "w") as delivery_report_stream:
            delivery_report_stream.write(delivery_report)
        return report_file_path

    def add_delivery_report_to_hk(
        self, case_id: str, delivery_report_file: Path, version: Version
    ) -> File | None:
        """Add a delivery report file to a case bundle and return its file object."""
        LOG.info(f"Adding a new delivery report to housekeeper for {case_id}")
        file: File = self.housekeeper_api.add_file(
            path=delivery_report_file,
            version_obj=version,
            tags=[
                case_id,
                HK_DELIVERY_REPORT_TAG,
                HermesFileTag.CLINICAL_DELIVERY,
                HermesFileTag.LONG_TERM_STORAGE,
            ],
        )
        self.housekeeper_api.include_file(file, version)
        self.housekeeper_api.add_commit(file)
        return file

    def get_delivery_report_from_hk(self, case_id: str, version: Version) -> str | None:
        """Return path of a delivery report stored in HK."""
        delivery_report: File = self.housekeeper_api.get_latest_file(
            bundle=case_id, tags=[HK_DELIVERY_REPORT_TAG], version=version.id
        )
        if not delivery_report:
            LOG.warning(f"No delivery report found in housekeeper for {case_id}")
            return None
        return delivery_report.full_path

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> str | None:
        """Return file path of the uploaded to Scout file given its tag."""
        version: Version = self.housekeeper_api.last_version(bundle=case_id)
        tags: list = self.get_hk_scout_file_tags(scout_tag=scout_tag)
        uploaded_file: File = self.housekeeper_api.get_latest_file(
            bundle=case_id, tags=tags, version=version.id
        )
        if not tags or not uploaded_file:
            LOG.warning(
                f"No files were found for the following Scout Housekeeper tag: {scout_tag} (case: {case_id})"
            )
            return None
        return uploaded_file.full_path

    @staticmethod
    def render_delivery_report(report_data: dict) -> str:
        """Renders the report on the Jinja template."""
        env = Environment(
            loader=PackageLoader("cg", "meta/report/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        env.globals["get_content_from_file"] = ReadFile.get_content_from_file
        env.globals["swedac_logo_path"] = SWEDAC_LOGO_PATH
        template: Template = env.get_template(name=DELIVERY_REPORT_FILE_NAME)
        return template.render(**report_data)

    def get_cases_without_delivery_report(self, workflow: Workflow) -> list[Case]:
        """Returns a list of cases that has been stored and need a delivery report."""
        stored_cases: list[Case] = []
        analyses: Query = self.status_db.analyses_to_delivery_report(workflow=workflow)[
            :MAX_ITEMS_TO_RETRIEVE
        ]
        for analysis in analyses:
            case: Case = analysis.case
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

    def get_cases_without_uploaded_delivery_report(self, workflow: Workflow) -> list[Case]:
        """Returns a list of cases that need a delivery report to be uploaded."""
        analyses: Query = self.status_db.analyses_to_upload_delivery_reports(workflow=workflow)[
            :MAX_ITEMS_TO_RETRIEVE
        ]
        return [analysis.case for analysis in analyses]

    def update_delivery_report_date(self, case: Case, analysis_date: datetime) -> None:
        """Updates the date when a delivery report was created."""
        analysis: Analysis = self.status_db.get_analysis_by_case_entry_id_and_started_at(
            case_entry_id=case.id, started_at_date=analysis_date
        )
        analysis.delivery_report_created_at = datetime.now()
        self.status_db.session.commit()

    def get_report_data(self, case_id: str, analysis_date: datetime) -> ReportModel:
        """Fetches all the data needed to generate a delivery report."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
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
            accredited=self.is_report_accredited(
                samples=case_model.samples, analysis_metadata=analysis_metadata
            ),
        )

    def validate_report_fields(self, case_id: str, report_data: ReportModel, force) -> ReportModel:
        """Verifies that the required report fields are not empty."""
        required_fields: dict = self.get_required_fields(case=report_data.case)
        empty_report_fields: dict = get_empty_report_data(report_data=report_data)
        missing_report_fields: dict = get_missing_report_data(
            empty_fields=empty_report_fields, required_fields=required_fields
        )
        if missing_report_fields and not force:
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
    def get_customer_data(case: Case) -> CustomerModel:
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
            version = len(analysis.case.analyses) - analysis.case.analyses.index(analysis)
        return version

    def get_case_data(
        self,
        case: Case,
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
            data_analysis=self.get_case_analysis_data(case=case, analysis=analysis),
            samples=samples,
            applications=unique_applications,
        )

    def get_samples_data(self, case: Case, analysis_metadata: AnalysisModel) -> list[SampleModel]:
        """Extracts all the samples associated to a specific case and their attributes."""
        samples = list()
        case_samples: list[CaseSample] = self.status_db.get_case_samples_by_case_id(
            case_internal_id=case.internal_id
        )
        for case_sample in case_samples:
            sample: Sample = case_sample.sample
            lims_sample: dict[str, Any] = self.lims_api.sample(sample.internal_id)
            delivered_files: list[File] | None = (
                self.delivery_api.get_analysis_sample_delivery_files_by_sample(
                    case=case, sample=sample
                )
                if self.delivery_api.is_analysis_delivery(case.data_delivery)
                else None
            )
            delivered_fastq_files: list[File] | None = (
                self.delivery_api.get_fastq_delivery_files_by_sample(case=case, sample=sample)
                if self.delivery_api.is_fastq_delivery(case.data_delivery)
                else None
            )
            samples.append(
                SampleModel(
                    name=sample.name,
                    id=sample.internal_id,
                    ticket=sample.original_ticket,
                    gender=sample.sex,
                    source=lims_sample.get("source"),
                    tumour=sample.is_tumour,
                    application=self.get_sample_application(sample=sample, lims_sample=lims_sample),
                    methods=self.get_sample_methods_data(sample_id=sample.internal_id),
                    status=case_sample.status,
                    metadata=self.get_sample_metadata(
                        case=case, sample=sample, analysis_metadata=analysis_metadata
                    ),
                    timestamps=self.get_sample_timestamp_data(sample=sample),
                    delivered_files=delivered_files,
                    delivered_fastq_files=delivered_fastq_files,
                )
            )
        return samples

    def get_workflow_accreditation_limitation(self, application_tag: str) -> str | None:
        """Return workflow specific limitations given an application tag."""
        application_limitation: ApplicationLimitations = (
            self.status_db.get_application_limitation_by_tag_and_workflow(
                tag=application_tag, workflow=self.analysis_api.workflow
            )
        )
        return application_limitation.limitations if application_limitation else None

    def get_sample_application(
        self, sample: Sample, lims_sample: dict[str:Any]
    ) -> ApplicationModel:
        """Return the analysis application attributes for a sample."""
        application: Application = self.status_db.get_application_by_tag(
            tag=lims_sample.get("application")
        )
        return (
            ApplicationModel(
                tag=application.tag,
                version=sample.application_version.version,
                prep_category=application.prep_category,
                description=application.description,
                details=application.details,
                limitations=application.limitations,
                workflow_limitations=self.get_workflow_accreditation_limitation(application.tag),
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
        prep_method: str | None = self.lims_api.get_prep_method(lims_id=sample_id)
        sequencing_method: str | None = self.lims_api.get_sequencing_method(lims_id=sample_id)
        return MethodsModel(library_prep=prep_method, sequencing=sequencing_method)

    def get_case_analysis_data(self, case: Case, analysis: Analysis) -> DataAnalysisModel:
        """Return workflow attributes used for data analysis."""
        delivered_files: list[File] | None = (
            self.delivery_api.get_analysis_case_delivery_files(case)
            if self.delivery_api.is_analysis_delivery(case.data_delivery)
            else None
        )
        return DataAnalysisModel(
            customer_workflow=case.data_analysis,
            data_delivery=case.data_delivery,
            delivered_files=delivered_files,
            genome_build=self.analysis_api.get_genome_build(case.internal_id),
            panels=case.panels,
            pons=self.analysis_api.get_pons(case.internal_id),
            scout_files=self.get_scout_uploaded_files(case.internal_id),
            type=self.analysis_api.get_data_analysis_type(case.internal_id),
            variant_callers=self.analysis_api.get_variant_callers(case.internal_id),
            workflow=analysis.workflow,
            workflow_version=analysis.workflow_version,
        )

    def get_scout_uploaded_files(self, case_id: str) -> ScoutReportFiles:
        """Return files that will be uploaded to Scout."""
        return ScoutReportFiles()

    @staticmethod
    def get_sample_timestamp_data(sample: Sample) -> TimestampModel:
        """Return sample processing dates."""
        return TimestampModel(
            ordered_at=sample.ordered_at,
            received_at=sample.received_at,
            prepared_at=sample.prepared_at,
            reads_updated_at=sample.last_sequenced_at,
        )

    def get_sample_metadata(
        self,
        case: Case,
        sample: Sample,
        analysis_metadata: AnalysisModel,
    ) -> SampleMetadataModel:
        """Return sample metadata to include in the report."""
        raise NotImplementedError

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Return whether the delivery report is accredited."""
        raise NotImplementedError

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields."""
        raise NotImplementedError

    @staticmethod
    def get_application_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Return sample required fields."""
        required_sample_fields = dict()
        for application in case.applications:
            required_sample_fields.update({application.tag: required_fields})
        return required_sample_fields

    @staticmethod
    def get_sample_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Return sample required fields."""
        required_sample_fields = dict()
        for sample in case.samples:
            required_sample_fields.update({sample.id: required_fields})
        return required_sample_fields

    @staticmethod
    def get_timestamp_required_fields(case: CaseModel, required_fields: list) -> dict:
        """Return sample timestamps required fields."""
        for sample in case.samples:
            if sample.application.external:
                required_fields.remove("received_at")
                break
        return ReportAPI.get_sample_required_fields(case=case, required_fields=required_fields)

    def get_hk_scout_file_tags(self, scout_tag: str) -> list | None:
        """Return workflow specific uploaded to Scout Housekeeper file tags given a Scout key."""
        tags = self.get_upload_case_tags().get(scout_tag)
        return list(tags) if tags else None

    def get_upload_case_tags(self):
        """Return workflow specific upload case tags."""
        raise NotImplementedError
