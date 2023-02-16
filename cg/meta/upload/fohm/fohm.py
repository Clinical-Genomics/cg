import logging
import getpass
import paramiko
import shutil
from pathlib import Path
from typing import List, Optional
import datetime as dt
import pandas as pd

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants.constants import SARS_COV_REGEX
from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.models.email import EmailInfo
from cg.store import Store, models
from cg.utils.email import send_mail
from housekeeper.store.models import Version

LOG = logging.getLogger(__name__)


class FOHMUploadAPI:
    def __init__(self, config: CGConfig, dry_run: bool = False, datestr: Optional[str] = None):
        self.config: CGConfig = config
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db
        self._dry_run: bool = dry_run
        self._current_datestr: str = datestr or str(dt.date.today())
        self._daily_bundle_path = None
        self._daily_rawdata_path = None
        self._daily_report_path = None
        self._cases_to_aggregate: List[str] = []
        self._daily_reports_list: List[Path] = []
        self._daily_pangolin_list: List[Path] = []
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
    def daily_reports_list(self) -> List[Path]:
        if not self._daily_reports_list:
            for case_id in self._cases_to_aggregate:
                self._daily_reports_list.append(
                    self.housekeeper_api.get_file_from_latest_version(
                        bundle_name=case_id, tags=["komplettering"]
                    ).full_path
                )
        return self._daily_reports_list

    @property
    def daily_pangolin_list(self) -> List[Path]:
        if not self._daily_pangolin_list:
            for case_id in self._cases_to_aggregate:
                self._daily_pangolin_list.append(
                    self.housekeeper_api.get_file_from_latest_version(
                        bundle_name=case_id, tags=["pangolin-typing-fohm"]
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
        LOG.info(f"Creating direcroty: {self.daily_rawdata_path}")
        LOG.info(f"Creating direcroty: {self.daily_report_path}")
        if self._dry_run:
            return
        self.daily_rawdata_path.mkdir(parents=True, exist_ok=True)
        self.daily_report_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_joined_dataframe(file_list: List[Path]) -> pd.DataFrame:
        """Creates dataframe with all csv files used in daily delivery"""
        dataframe_list = [pd.read_csv(filename, index_col=None, header=0) for filename in file_list]
        return pd.concat(dataframe_list, axis=0, ignore_index=True)

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
            sample_obj: models.Sample = self.status_db.sample(sample_id)
            bundle_name = sample_obj.links[0].family.internal_id
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

    def send_mail_reports(self) -> None:
        for file in self.daily_report_path.iterdir():
            LOG.info(
                f"Sending {file.name} report file to {self.config.fohm.email_recipient}, dry run: {self._dry_run}"
            )
            if self._dry_run:
                return
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
            sftp.put(file.as_posix(), f"/till-fohm/{file.name}")
            LOG.info(f"Finished sending {file}")
        sftp.close()
        transport.close()

    def update_upload_started_at(self, case_id: str) -> None:
        """Update timestamp for cases which started being processed as batch"""
        if self._dry_run:
            return
        case_obj: models.Family = self.status_db.family(case_id)
        case_obj.analyses[0].upload_started_at = dt.datetime.now()
        self.status_db.commit()

    def update_uploaded_at(self, case_id: str) -> None:
        """Update timestamp for cases which uploaded successfully"""
        if self._dry_run:
            return
        case_obj: models.Family = self.status_db.family(case_id)
        case_obj.analyses[0].uploaded_at = dt.datetime.now()
        self.status_db.commit()
