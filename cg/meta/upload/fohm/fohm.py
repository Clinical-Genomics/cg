import datetime as dt
import getpass
import logging
import os
import re
import shutil
from pathlib import Path

import pandas as pd
import paramiko
from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants import FileExtensions
from cg.constants.constants import SARS_COV_REGEX, FileFormat
from cg.constants.housekeeper_tags import FohmTag
from cg.exc import CgError
from cg.io.controller import ReadFile
from cg.io.csv import write_csv_from_dict
from cg.models.cg_config import CGConfig
from cg.models.email import EmailInfo
from cg.models.fohm.reports import FohmComplementaryReport, FohmPangolinReport
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils.dict import remove_duplicate_dicts
from cg.utils.email import send_mail

LOG = logging.getLogger(__name__)


def create_daily_deliveries_csv(file_paths: list[Path]) -> list[dict]:
    """Creates a list of dicts with all CSV files used in daily delivery."""
    all_deliveries = [
        ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=file_path, read_to_dict=True
        )
        for file_path in file_paths
    ]
    dicts = []
    for list_with_dicts in all_deliveries:
        dicts.extend(iter(list_with_dicts))
    return dicts


def validate_fohm_complementary_reports(reports: list[dict]) -> list[FohmComplementaryReport]:
    """Validate FOHM complementary reports.
    Raises: ValidateError"""
    complementary_reports = []
    for report in reports:
        complementary_report = FohmComplementaryReport.model_validate(report)
        complementary_reports.append(complementary_report)
    return complementary_reports


def validate_fohm_pangolin_reports(reports: list[dict]) -> list[FohmPangolinReport]:
    """Validate FOHM Pangolin reports.
    Raises: ValidateError"""
    pangolin_reports = []
    for report in reports:
        pangolin_report = FohmPangolinReport.model_validate(report)
        pangolin_reports.append(pangolin_report)
    return pangolin_reports


def get_sars_cov_complementary_reports(
    reports: list[FohmComplementaryReport],
) -> list[FohmComplementaryReport]:
    """Return all "Sars-cov2" reports from multiple cases."""
    return [report for report in reports if re.search(SARS_COV_REGEX, report.sample_number)]


def get_sars_cov_pangolin_reports(reports: list[FohmPangolinReport]) -> list[FohmPangolinReport]:
    """Return all "Sars-cov2" reports from multiple cases."""
    return [report for report in reports if re.search(SARS_COV_REGEX, report.taxon)]


class FOHMUploadAPI:
    def __init__(self, config: CGConfig, dry_run: bool = False, datestr: str | None = None):
        self.config: CGConfig = config
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db
        self._dry_run: bool = dry_run
        self._current_datestr: str = datestr or str(dt.date.today())
        self._daily_bundle_path = None
        self._daily_rawdata_path = None
        self._daily_report_path = None
        self._cases_to_aggregate: list[str] = []
        self._daily_reports_list: list[Path] = []
        self._daily_pangolin_list: list[Path] = []
        self._reports_dataframe = None
        self._pangolin_dataframe = None
        self._aggregation_dataframe = None

    @property
    def current_datestr(self) -> str:
        if not self._current_datestr:
            self._current_datestr = str(dt.date.today())
        return self._current_datestr

    @property
    def daily_bundle_path(self) -> Path:
        if not self._daily_bundle_path:
            self._daily_bundle_path: Path = Path(
                Path(self.config.mutant.root).parent, "fohm", self.current_datestr
            )
        return self._daily_bundle_path

    @property
    def daily_rawdata_path(self) -> Path:
        if not self._daily_rawdata_path:
            self._daily_rawdata_path: Path = Path(self.daily_bundle_path, "rawdata")
        return self._daily_rawdata_path

    @property
    def daily_report_path(self) -> Path:
        if not self._daily_report_path:
            self._daily_report_path: Path = Path(self.daily_bundle_path, "reports")
        return self._daily_report_path

    @property
    def reports_dataframe(self) -> pd.DataFrame:
        """Dataframe with all 'komplettering' rows from multiple cases"""
        if not isinstance(self._reports_dataframe, pd.DataFrame):
            self._reports_dataframe = self.create_joined_dataframe(
                self.daily_reports_list
            ).sort_values(by=["provnummer"])
            self._reports_dataframe.drop_duplicates(inplace=True, ignore_index=True)
            self._reports_dataframe = self._reports_dataframe[
                self._reports_dataframe["provnummer"].str.contains(SARS_COV_REGEX)
            ].reset_index(drop=True)
        return self._reports_dataframe

    @property
    def pangolin_dataframe(self) -> pd.DataFrame:
        """Dataframe with all pangolin rows from multiple cases"""
        if not isinstance(self._pangolin_dataframe, pd.DataFrame):
            self._pangolin_dataframe = self.create_joined_dataframe(
                self.daily_pangolin_list
            ).sort_values(by=["taxon"])
            self._pangolin_dataframe.drop_duplicates(inplace=True, ignore_index=True)
            self._pangolin_dataframe = self.pangolin_dataframe[
                self._pangolin_dataframe["taxon"].str.contains(SARS_COV_REGEX)
            ].reset_index(drop=True)
        return self._pangolin_dataframe

    @property
    def aggregation_dataframe(self) -> pd.DataFrame:
        """Dataframe with all 'komplettering' rows from multiple cases, and additional rows to be
        used for aggregation."""
        if not isinstance(self._aggregation_dataframe, pd.DataFrame):
            self._aggregation_dataframe = self.reports_dataframe.copy()
        return self._aggregation_dataframe

    @property
    def daily_reports_list(self) -> list[Path]:
        if not self._daily_reports_list:
            for case_id in self._cases_to_aggregate:
                self._daily_reports_list.append(
                    self.housekeeper_api.get_file_from_latest_version(
                        bundle_name=case_id, tags=[FohmTag.Complementary]
                    ).full_path
                )
        return self._daily_reports_list

    @property
    def daily_pangolin_list(self) -> list[Path]:
        if not self._daily_pangolin_list:
            for case_id in self._cases_to_aggregate:
                self._daily_pangolin_list.append(
                    self.housekeeper_api.get_file_from_latest_version(
                        bundle_name=case_id, tags=[FohmTag.PANGOLIN_TYPING]
                    ).full_path
                )
        return self._daily_pangolin_list

    @property
    def dry_run(self):
        return self._dry_run

    def check_username(self) -> None:
        if self._dry_run:
            return
        if getpass.getuser() == self.config.fohm.valid_uploader:
            return
        raise CgError(
            f"Cannot upload to FOHM as {getpass.getuser()}, please log in as {self.config.fohm.valid_uploader} "
        )

    def set_cases_to_aggregate(self, cases: list) -> None:
        LOG.info(f"Preparing aggregated delivery for {cases}")
        self._cases_to_aggregate = cases

    def create_daily_delivery_folders(self) -> None:
        LOG.info(f"Creating directory: {self.daily_rawdata_path}")
        LOG.info(f"Creating directory: {self.daily_report_path}")
        if self._dry_run:
            return
        self.daily_rawdata_path.mkdir(parents=True, exist_ok=True)
        self.daily_report_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_joined_dataframe(file_list: list[Path]) -> pd.DataFrame:
        """Creates dataframe with all csv files used in daily delivery"""
        dataframe_list = [pd.read_csv(filename, index_col=None, header=0) for filename in file_list]
        return pd.concat(dataframe_list, axis=0, ignore_index=True)

    def add_sample_internal_id_complementary_report(
        self, reports: list[FohmComplementaryReport]
    ) -> None:
        """Add sample internal id to complementary reports."""
        for report in reports:
            report.internal_id = self.status_db.get_sample_by_name(
                name=report.sample_number
            ).internal_id

    def add_sample_internal_id_pangolin_report(self, reports: list[FohmPangolinReport]) -> None:
        """Add sample internal id to Pangolin reports."""
        for report in reports:
            report.internal_id = self.status_db.get_sample_by_name(name=report.taxon).internal_id

    def add_region_lab_to_reports(
        self, reports: list[FohmComplementaryReport] | list[FohmPangolinReport]
    ) -> None:
        """Add region lab to reports."""
        for report in reports:
            report.region_lab = f"""{self.lims_api.get_sample_attribute(lims_id=report.internal_id, key="region_code").split(' ')[0]}"""
            f"""_{self.lims_api.get_sample_attribute(lims_id=report.internal_id, key="lab_code").split(' ')[0]}"""

    def append_metadata_to_aggregation_df(self) -> None:
        """
        Add fields with internal_id and region_lab to dataframe
        """

        self.aggregation_dataframe["internal_id"] = self.aggregation_dataframe["provnummer"].apply(
            lambda x: self.status_db.get_sample_by_name(name=x).internal_id
        )
        self.aggregation_dataframe["region_lab"] = self.aggregation_dataframe["internal_id"].apply(
            lambda x: f"{self.lims_api.get_sample_attribute(lims_id=x, key='region_code').split(' ')[0]}"
            f"_{self.lims_api.get_sample_attribute(lims_id=x, key='lab_code').split(' ')[0]}"
        )

    def link_sample_rawdata_files(self) -> None:
        """Hardlink samples rawdata files to fohm delivery folder."""
        for sample_id in self.aggregation_dataframe["internal_id"]:
            sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
            bundle_name = sample.links[0].case.internal_id
            version_obj: Version = self.housekeeper_api.last_version(bundle=bundle_name)
            files = self.housekeeper_api.files(version=version_obj.id, tags=[sample_id]).all()
            for file in files:
                if self._dry_run:
                    LOG.info(
                        f"Would have copied {file.full_path} to {Path(self.daily_rawdata_path)}"
                    )
                    continue
                shutil.copy(file.full_path, Path(self.daily_rawdata_path))

    def link_sample_rawdata_files_csv(
        self, reports: list[FohmComplementaryReport] | list[FohmPangolinReport]
    ) -> None:
        """Hardlink samples raw data files to FOHM delivery folder."""
        for report in reports:
            for sample_id in report.internal_id:
                sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
                bundle_name = sample.links[0].case.internal_id
                version_obj: Version = self.housekeeper_api.last_version(bundle=bundle_name)
                files = self.housekeeper_api.files(version=version_obj.id, tags=[sample_id]).all()
                for file in files:
                    if self._dry_run:
                        LOG.info(
                            f"Would have copied {file.full_path} to {Path(self.daily_rawdata_path)}"
                        )
                        continue
                    shutil.copy(file.full_path, Path(self.daily_rawdata_path))

    def create_pangolin_reports(self) -> None:
        LOG.info("Creating pangolin reports")
        unique_regionlabs = list(self.aggregation_dataframe["region_lab"].unique())
        LOG.info(f"Regions in batch: {unique_regionlabs}")
        for region_lab in unique_regionlabs:
            LOG.info(f"Aggregating data for {region_lab}")
            pangolin_df = self.pangolin_dataframe[
                self.aggregation_dataframe["region_lab"] == region_lab
            ]
            if self._dry_run:
                LOG.info(pangolin_df)
                continue
            pangolin_path = Path(
                self.daily_rawdata_path,
                f"{region_lab}_{self.current_datestr}_pangolin_classification_format4.txt",
            )
            pangolin_df.to_csv(
                pangolin_path,
                sep="\t",
                index=False,
            )
            pangolin_path.chmod(0o0777)

    def create_pangolin_report_csv(self, reports: list[FohmPangolinReport]) -> None:
        LOG.info("Creating aggregate Pangolin report")
        unique_region_labs: set[str] = {report.region_lab for report in reports}
        LOG.info(f"Regions in batch: {unique_region_labs}")
        for region_lab in unique_region_labs:
            LOG.info(f"Aggregating data for {region_lab}")
            region_lab_reports: list[FohmPangolinReport] = [
                report for report in reports if report.region_lab == region_lab
            ]
            if self._dry_run:
                LOG.info(region_lab_reports)
                continue
            pangolin_report_file = Path(
                self.daily_rawdata_path,
                f"{region_lab}_{self.current_datestr}_pangolin_classification_format4{FileExtensions.TXT}",
            )
            all_region_lab_reports: list[dict] = [
                report.model_dump() for report in region_lab_reports
            ]
            fieldnames: list[str] = sorted(region_lab_reports[0].model_dump().keys())
            write_csv_from_dict(
                content=all_region_lab_reports,
                fieldnames=fieldnames,
                file_path=pangolin_report_file,
            )
            pangolin_report_file.chmod(0o0777)

    def create_komplettering_reports(self) -> None:
        LOG.info("Creating komplettering reports")
        unique_regionlabs = list(self.aggregation_dataframe["region_lab"].unique())
        LOG.info(f"Regions in batch: {unique_regionlabs}")
        for region_lab in unique_regionlabs:
            LOG.info(f"Aggregating data for {region_lab}")
            report_df = self.reports_dataframe[
                self.aggregation_dataframe["region_lab"] == region_lab
            ]
            if self._dry_run:
                LOG.info(report_df)
                continue
            report_df.to_csv(
                self.daily_report_path / f"{region_lab}_{self.current_datestr}_komplettering.csv",
                sep=",",
                index=False,
            )

    def create_complementary_report_csv(self, reports: list[FohmComplementaryReport]) -> None:
        LOG.info("Creating aggregate 'komplettering' report")
        unique_region_labs: set[str] = {report.region_lab for report in reports}
        LOG.info(f"Regions laboratories  in batch: {unique_region_labs}")
        for region_lab in unique_region_labs:
            LOG.info(f"Aggregating data for {region_lab}")
            region_lab_reports: list[FohmComplementaryReport] = [
                report for report in reports if report.region_lab == region_lab
            ]
            if self._dry_run:
                LOG.info(region_lab_reports)
                continue
            all_region_lab_reports: list[dict] = [
                report.model_dump() for report in region_lab_reports
            ]
            fieldnames: list[str] = sorted(region_lab_reports[0].model_dump().keys())
            complementary_report_file = Path(
                self.daily_report_path,
                f"{region_lab}_{self.current_datestr}_komplettering{FileExtensions.CSV}",
            )
            write_csv_from_dict(
                content=all_region_lab_reports,
                fieldnames=fieldnames,
                file_path=complementary_report_file,
            )

    def send_mail_reports(self) -> None:
        for file in self.daily_report_path.iterdir():
            LOG.info(
                f"Sending {file.name} report file to {self.config.fohm.email_recipient}, dry run: {self._dry_run}"
            )
            if self._dry_run:
                return

            try:
                send_mail(
                    EmailInfo(
                        receiver_email=self.config.fohm.email_recipient,
                        sender_email=self.config.fohm.email_sender,
                        smtp_server=self.config.fohm.email_host,
                        subject=file.name,
                        message=" ",
                        file=file,
                    )
                )
                file.unlink()

            except Exception as ex:
                LOG.error(f"Failed sending email report {file} with error: {ex}")

        if os.listdir(self.daily_report_path) == []:
            self.daily_report_path.rmdir()

        if os.listdir(self.daily_bundle_path) == []:
            self.daily_bundle_path.rmdir()

    def sync_files_sftp(self) -> None:
        self.check_username()
        transport = paramiko.Transport((self.config.fohm.host, self.config.fohm.port))
        ed_key = paramiko.Ed25519Key.from_private_key_file(self.config.fohm.key)
        transport.connect(username=self.config.fohm.username, pkey=ed_key)
        sftp = paramiko.SFTPClient.from_transport(transport)
        for file in self.daily_rawdata_path.iterdir():
            LOG.info(f"Sending {file} via SFTP, dry-run {self.dry_run}")
            if self._dry_run:
                continue

            try:
                sftp.put(file.as_posix(), f"/till-fohm/{file.name}")
                LOG.info(f"Finished sending {file}")
                file.unlink()
            except Exception as ex:
                LOG.error(f"Failed sending {file} with error: {ex}")

        sftp.close()
        transport.close()

        if os.listdir(self.daily_rawdata_path) == []:
            self.daily_rawdata_path.rmdir()

    def update_upload_started_at(self, case_id: str) -> None:
        """Update timestamp for cases which started being processed as batch"""
        if self._dry_run:
            return
        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        case_obj.analyses[0].upload_started_at = dt.datetime.now()
        self.status_db.session.commit()

    def update_uploaded_at(self, case_id: str) -> None:
        """Update timestamp for a case which uploaded successfully."""
        if self._dry_run:
            return
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        case.analyses[0].uploaded_at = dt.datetime.now()
        self.status_db.session.commit()

    def parse_write_complementary_report(self) -> list[FohmComplementaryReport]:
        """Create and write a complementary report."""
        complementary_reports_raw: list[dict] = create_daily_deliveries_csv(self.daily_reports_list)
        unique_complementary_reports_raw: list[dict] = remove_duplicate_dicts(
            complementary_reports_raw
        )
        complementary_reports: list[FohmComplementaryReport] = validate_fohm_complementary_reports(
            unique_complementary_reports_raw
        )
        complementary_reports: list[FohmComplementaryReport] = get_sars_cov_complementary_reports(
            complementary_reports
        )
        self.add_sample_internal_id_complementary_report(complementary_reports)
        self.add_region_lab_to_reports(complementary_reports)
        self.create_complementary_report_csv(complementary_reports)
        return complementary_reports

    def parse_and_write_pangolin_report(self) -> list[FohmPangolinReport]:
        """Create and write a Pangolin report."""
        pangolin_reports_raw: list[dict] = create_daily_deliveries_csv(self.daily_pangolin_list)
        unique_pangolin_reports_raw: list[dict] = remove_duplicate_dicts(pangolin_reports_raw)
        pangolin_reports: list[FohmPangolinReport] = validate_fohm_pangolin_reports(
            unique_pangolin_reports_raw
        )
        pangolin_reports: list[FohmPangolinReport] = get_sars_cov_pangolin_reports(pangolin_reports)
        self.add_sample_internal_id_pangolin_report(pangolin_reports)
        self.add_region_lab_to_reports(pangolin_reports)
        self.create_pangolin_report_csv(pangolin_reports)
        return pangolin_reports

    def aggregate_delivery(self, cases: list[str]) -> None:
        """Aggregate and hardlink reports."""
        self.set_cases_to_aggregate(cases)
        self.create_daily_delivery_folders()
        complementary_reports: list[FohmComplementaryReport] = (
            self.parse_write_complementary_report()
        )
        self.link_sample_rawdata_files_csv(complementary_reports)
        pangolin_reports: list[FohmPangolinReport] = self.parse_and_write_pangolin_report()
        self.link_sample_rawdata_files_csv(pangolin_reports)

    def create_complementary_report(self, cases: list[str]) -> None:
        """Create and write a complementary report."""
        self.set_cases_to_aggregate(cases)
        self.create_daily_delivery_folders()
        self.parse_write_complementary_report()
