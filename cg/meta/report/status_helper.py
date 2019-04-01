"""Class that fetches and calculates data from status database """


class StatusHelper:
    """Class that fetches and calculates data from status database """

    @staticmethod
    def get_report_version(analysis):
        """Returns the version for the given analysis where the primary analysis is 1 and
        subsequent reruns increase the version by for each"""

        version = None

        if analysis:
            version = str(analysis.family.analyses.index(analysis) + 1)

        return version
