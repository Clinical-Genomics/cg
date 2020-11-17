import requests


class NIPToolAPI:
    """Class handling upload of analyses to NIPTool
    Needs:
        NIPT upload service account
        request constructor

        send result file with post
        send multiqc file with post
        send samplesheet with post
        ???
        Profit

    """

    def __init__(self, config):
        self.config = config
