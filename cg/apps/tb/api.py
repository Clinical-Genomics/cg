""" Trailblazer API for cg """ ""
import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from cg.utils import Process

import click
import ruamel.yaml
from trailblazer.mip.start import MipCli
from trailblazer.store import api, models, Store
from trailblazer.mip import files, trending

LOG = logging.getLogger(__name__)


class TrailblazerAPI(Store):
    """Interface to Trailblazer for `cg`."""

    parse_sampleinfo = staticmethod(files.parse_sampleinfo)

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config["trailblazer"]["database"],
            families_dir=config["trailblazer"]["root"],
        )
        self.mip_cli = MipCli(
            script=config["trailblazer"]["script"],
            pipeline=config["trailblazer"]["pipeline"],
            conda_env=config["trailblazer"]["conda_env"],
        )
        self.mip_config = config["trailblazer"]["mip_config"]
        self.process = Process(
            config_parameter="--config",
            config=config["trailblazer"]["config"],
            binary=config["trailblazer"]["binary_path"],
        )

    def mark_analyses_deleted(self, case_id: str):
        """ mark analyses connected to a case as deleted """
        for old_analysis in self.analyses(family=case_id):
            old_analysis.is_deleted = True
        self.commit()

    def add_pending_analysis(self, case_id: str, email: str = None) -> Optional[models.Analysis]:
        """ Add analysis as pending"""
        result = self.process.run_command(["query add-pending-analysis", case_id, email])
        if result != 0:
            LOG.info("Failed to add analysis as pending!")
            return None
        LOG.info(self.process.stdout)

    @staticmethod
    def get_sampleinfo(analysis: models.Analysis) -> str:
        """Get the sample info path for an analysis."""
        raw_data = ruamel.yaml.safe_load(Path(analysis.config_path).open())
        data = files.parse_config(raw_data)
        return data["sampleinfo_path"]

    @staticmethod
    def parse_qcmetrics(data: dict) -> dict:
        """Call internal Trailblazer MIP API."""
        return files.parse_qcmetrics(data)

    def is_analysis_ongoing(self, case_id: str) -> bool:
        """Call internal Trailblazer API"""
        return self.is_latest_analysis_ongoing(case_id=case_id)

    def is_analysis_failed(self, case_id: str) -> bool:
        """Call internal Trailblazer API"""
        return self.is_latest_analysis_failed(case_id=case_id)

    def is_analysis_completed(self, case_id: str) -> bool:
        """Call internal Trailblazer API"""
        return self.is_latest_analysis_completed(case_id=case_id)

    def get_analysis_status(self, case_id: str) -> str:
        """Call internal Trailblazer API"""
        return self.get_latest_analysis_status(case_id=case_id)

    def has_analysis_started(self, case_id: str) -> bool:
        """Check if analysis has started"""
        statuses = ("ongoing", "failed", "completed")
        get_analysis_status = {
            "ongoing": self.is_analysis_ongoing,
            "failed": self.is_analysis_failed,
            "completed": self.is_analysis_completed,
        }
        for status in statuses:
            has_started = get_analysis_status[status](case_id=case_id)
            if has_started:
                return has_started
        return False

    def delete_analysis(
        self,
        family: str,
        date: dt.datetime,
        yes: bool = False,
        dry_run: bool = False,
    ):
        """Delete the analysis output."""
        if self.analyses(family=family, temp=True).count() > 0:
            raise ValueError("analysis for family already running")
        analysis_obj = self.find_analysis(family, date, "completed")
        assert analysis_obj.is_deleted is False
        analysis_path = Path(analysis_obj.out_dir).parent

        if yes or click.confirm(f"Do you want to remove {analysis_path}?"):

            if not dry_run:
                shutil.rmtree(analysis_path, ignore_errors=True)
                analysis_obj.is_deleted = True
                self.commit()

    @staticmethod
    def get_trending(mip_config_raw: str, qcmetrics_raw: str, sampleinfo_raw: dict) -> dict:
        """Get trending data for a MIP analysis"""
        return trending.parse_mip_analysis(
            mip_config_raw=mip_config_raw,
            qcmetrics_raw=qcmetrics_raw,
            sampleinfo_raw=sampleinfo_raw,
        )

    def get_family_root_dir(self, family_id: str):
        """Get path for a case"""
        return Path(self.families_dir) / family_id

    def get_latest_logged_analysis(self, case_id: str):
        """Get the the analysis with the latest logged_at date"""
        return self.analyses(family=case_id).order_by(models.Analysis.logged_at.desc())

    @staticmethod
    def get_sampleinfo_date(data: dict) -> str:
        """Get date from a sampleinfo """
        return files.get_sampleinfo_date(data)
