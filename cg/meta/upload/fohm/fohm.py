import shutil
from pathlib import Path
from typing import List
import datetime as dt
import pandas as pd

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from housekeeper.store.models import Version


class FOHMUploadAPI:
    def __init__(self, config: CGConfig):
        self.config: CGConfig = config
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db

        self._current_datestr = None
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
            self._daily_bundle_path = (
                Path(self.config.mutant.root).parent / "fohm" / self.current_datestr
            )
        return self._daily_bundle_path

    @property
    def daily_rawdata_path(self) -> Path:
        if not self._daily_rawdata_path:
            self._daily_rawdata_path = self.daily_bundle_path / "rawdata"
        return self._daily_rawdata_path

    @property
    def daily_report_path(self) -> Path:
        if not self._daily_report_path:
            self._daily_report_path = self.daily_bundle_path / "reports"
        return self._daily_report_path

    @property
    def reports_dataframe(self) -> pd.DataFrame:
        """Dataframe with all komplettering rows from multiple cases"""
        if not isinstance(self._reports_dataframe, pd.DataFrame):
            self._reports_dataframe = self.create_joined_dataframe(
                self.daily_reports_list
            ).sort_values(by=["provnummer"])
        return self._reports_dataframe

    @property
    def pangolin_dataframe(self) -> pd.DataFrame:
        """Dataframe with all pangolin rows from multiple cases"""
        if not isinstance(self._pangolin_dataframe, pd.DataFrame):
            self._pangolin_dataframe = self.create_joined_dataframe(
                self.daily_pangolin_list
            ).sort_values(by=["taxon"])
        return self._pangolin_dataframe

    @property
    def aggregation_dataframe(self) -> pd.DataFrame:
        """Dataframe with all komplettering rows from multiple cases, and additional rows to be used for aggregation"""
        if not isinstance(self._aggregation_dataframe, pd.DataFrame):
            self._aggregation_dataframe = self.reports_dataframe.copy()
        return self._aggregation_dataframe

    @property
    def daily_reports_list(self) -> List[Path]:
        if not self._daily_reports_list:
            for case_id in self._cases_to_aggregate:
                self._daily_reports_list.append(
                    self.housekeeper_api.find_file_in_latest_version(
                        case_id=case_id, tags=["komplettering"]
                    ).full_path
                )
        return self._daily_reports_list

    @property
    def daily_pangolin_list(self) -> List[Path]:
        if not self._daily_pangolin_list:
            for case_id in self._cases_to_aggregate:
                self._daily_pangolin_list.append(
                    self.housekeeper_api.find_file_in_latest_version(
                        case_id=case_id, tags=["pangolin-typing-fohm"]
                    ).full_path
                )
        return self._daily_pangolin_list

    def create_daily_delivery_folders(self) -> None:
        self.daily_rawdata_path.mkdir(parents=True, exist_ok=True)
        self.daily_report_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_joined_dataframe(file_list: List[Path]) -> pd.DataFrame:
        """Creates datafame with all csv files used in daily delivery"""
        dataframe_list = [pd.read_csv(filename, index_col=None, header=0) for filename in file_list]
        return pd.concat(dataframe_list, axis=0, ignore_index=True)

    def append_metadata_to_aggregation_df(self) -> None:
        """Add field with internal_id to dataframe
        TODO: get internal_id from sample_id
        """

        self.aggregation_dataframe["internal_id"] = self.aggregation_dataframe["provnummer"].apply(
            lambda x: self.status_db.samples_by_ids(name=x).first().internal_id
        )
        self.aggregation_dataframe["region_lab"] = self.aggregation_dataframe["internal_id"].apply(
            lambda x: f"{self.lims_api.get_sample_attribute(lims_id=x, key='region_code').split(' ')[0]}"
            f"_{self.lims_api.get_sample_attribute(lims_id=x, key='lab_code').split(' ')[0]}"
        )

    def link_sample_rawdata(self) -> None:
        """Hardlink samples rawdata files to fohm delivery folder
        TODO: for each sample_internal_id, find case_id, then find corresponding HK bundle, and link sample rawdata
        """
        for sample_id in self.aggregation_dataframe["internal_id"]:
            sample_obj: models.Sample = self.status_db.sample(sample_id)
            bundle_name = sample_obj.links[0].family.internal_id
            version_obj: Version = self.housekeeper_api.last_version(bundle=bundle_name)
            files = self.housekeeper_api.files(version=version_obj.id, tags=[sample_id]).all()
            for file in files:
                shutil.copy(file.full_path, Path(self.daily_rawdata_path))

    def reaggregate_reports(self):
        unique_regionlabs = list(self.aggregation_dataframe["region_lab"].unique())
        for region_lab in unique_regionlabs:
            pangolin_df = self.pangolin_dataframe[
                self.aggregation_dataframe["region_lab"] == region_lab
            ]
            pangolin_df.to_csv(
                self.daily_rawdata_path
                / f"{region_lab}_{self.current_datestr}_pangolin_classification_format3.txt",
                sep="\t",
                index=False,
            )
            report_df = self.reports_dataframe[
                self.aggregation_dataframe["region_lab"] == region_lab
            ]
            report_df.to_csv(
                self.daily_report_path / f"{region_lab}_{self.current_datestr}_komplettering.csv",
                sep=",",
                index=False,
            )

    def assemble_fohm_delivery(self, cases: List[str]) -> None:
        """Rearrange data and put in delivery dir"""
        self._cases_to_aggregate = cases
        self.create_daily_delivery_folders()
        self.append_metadata_to_aggregation_df()
        self.link_sample_rawdata()

    def sync_delivery_dir(self, datestr: str = None):
        pass

    def send_mail_reports(self, datestr: str = None):
        pass

    def upload_daily_batch(self):
        self.sync_delivery_dir(datestr=self.current_datestr)
        self.send_mail_reports(datestr=self.current_datestr)

    def send_mail(self):
        """Send one email with one csv to FOHM"""
        pass

    def update_upload_started_at(self, case_id: str):
        """Update timestamp for cases which started being processed as batch"""
        case_obj: models.Family = self.status_db.family(case_id)
        case_obj.analyses[0].upload_started_at = dt.datetime.now()
        self.status_db.commit()

    def update_uploaded_at(self, case_id: str) -> None:
        """Update timestamp for cases which uploaded successfully"""
        case_obj: models.Family = self.status_db.family(case_id)
        case_obj.analyses[0].uploaded_at = dt.datetime.now()
        self.status_db.commit()
