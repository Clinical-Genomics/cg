from pathlib import Path
from typing import List
import datetime as dt
import pandas as pd

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models


class FOHMUploadAPI:
    def __init__(self, config: CGConfig):
        self.config: CGConfig = config
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db

        self.fohm_delivery_path = Path(config.mutant.root).parent / "fohm"
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
        if not self._current_date:
            self._current_date = str(dt.date.today)
        return self._current_date

    @property
    def daily_bundle_path(self) -> Path:
        if not self._daily_bundle_path:
            self._daily_bundle_path = self.fohm_delivery_path / self.current_datestr
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
        if not self._reports_dataframe:
            self._reports_dataframe = self.create_joined_dataframe(self._daily_reports_list)
        return self._reports_dataframe

    @property
    def pangolin_dataframe(self) -> pd.DataFrame:
        """Dataframe with all pangolin rows from multiple cases"""
        if not self._pangolin_dataframe:
            self._pangolin_dataframe = self.create_joined_dataframe(self._daily_pangolin_list)
        return self._pangolin_dataframe

    @property
    def aggregation_dataframe(self) -> pd.DataFrame:
        """Dataframe with all komplettering rows from multiple cases, and additional rows to be used for aggregation"""
        if not self._aggregation_dataframe:
            raise NotImplementedError
        return self._aggregation_dataframe

    def create_daily_delivery_folders(self) -> None:
        self.daily_rawdata_path.mkdir(parents=True, exist_ok=True)
        self.daily_report_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create_joined_dataframe(file_list: List[Path]) -> pd.DataFrame:
        """Creates datafame with all csv files used in daily delivery"""
        dataframe_list = [pd.read_csv(filename, index_col=None, header=0) for filename in file_list]
        return pd.concat(dataframe_list, axis=0, ignore_index=True)

    def parse_csv_from_bundles(self, cases: List[str]) -> None:
        """Get csv to aggregate from all bundles"""
        for case in cases:
            print("Will find csv in hk and append to list")
        pass

    def append_internal_id_to_aggregation_df(self) -> None:
        """Add field with internal_id to dataframe
        TODO: get internal_id from sample_id
        """
        pass

    def append_regionlab_to_aggregation_df(self) -> None:
        """Add field with regionlab to dataframe
        TODO: get regionlab from internal_id in lims
        """
        pass

    def link_sample_rawdata(self) -> None:
        """Hardlink samples rawdata files to fohm delivery folder
        TODO: for each sample_internal_id, find case_id, then find corresponding HK bundle, and link sample rawdata
        """
        pass

    def create_reaggregated_report_regionlab(self, region_lab: str) -> None:
        """Write separate komplettering csv report for regionlab"""
        pass

    def create_reaggregated_pangolin_regionlab(self, region_lab: str) -> None:
        """Write separate pangolin csv report for regionlab"""
        pass

    def assemble_fohm_delivery(self, cases: List[str]) -> None:
        self._cases_to_aggregate = cases
        """Rearrange data and put in delivery dir"""
        pass

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
