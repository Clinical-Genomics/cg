from typing import List
import datetime as dt
import logging
from cgbeacon.utils import Utility
from cgbeacon.utils.mysql_handler import use_mysqlalchemy

LOG = logging.getLogger(__name__)


class BeaconApi:
    """
        Interface with Beacon importer (github.com/Clinical-Genomics/cgbeacon)
        Inserts variants from a VCF file inside a Beacon server.
    """

    def __init__(self, config: dict):
        super(BeaconApi, self).__init__()
        self.connection = use_mysqlalchemy(config["cgbeacon"]["database"])

    def upload(
        self,
        vcf_path: str,
        panel_path: str,
        dataset: str,
        outfile: str,
        customer: str,
        samples: List[str],
        quality: int,
        genome_reference: str,
    ):
        """ Uploads variants from a VCF file to a MySQL Beacon database
            Returns: number of new variants in the Beacon
        """

        LOG.info("Uploading variants to beacon db.")
        upload_result = Utility.beacon_upload(
            self.connection,
            vcf_path,
            panel_path,
            dataset,
            outfile,
            customer,
            samples,
            quality,
            genome_reference,
        )
        LOG.info("Upload complete!")

    def remove_vars(self, sample, vcf_path, panel_path=None, qual=20):
        """ Calls Utility app in beacon package to remove vars from beacon
            Returns: number of new variants removed from the beacon
        """
        removed = Utility.beacon_clean(self.connection, sample, vcf_path, panel_path, qual)
        return removed
