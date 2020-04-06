"""Class that fetches and calculates data from status database """
from cg.store import models


class ReportHelper:
    """Class that fetches and calculates data from status database """

    @staticmethod
    def get_report_version(analysis: models.Analysis) -> int:
        """Returns the version for the given analysis where the primary analysis is 1 and
        subsequent reruns increase the version by for each"""

        version = None

        if analysis:
            version = len(analysis.family.analyses) - analysis.family.analyses.index(analysis)

        return version

    @staticmethod
    def get_previous_report_version(analysis: models.Analysis) -> int:
        """Returns the version for the analysis before the given analysis"""

        analysis_version = ReportHelper.get_report_version(analysis)
        previous_version = None

        if analysis_version and analysis_version > 1:
            previous_version = analysis_version - 1

        return previous_version
