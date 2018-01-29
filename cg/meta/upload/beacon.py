import logging
import datetime as dt
import time
from tempfile import NamedTemporaryFile

from cgbeacon.utils import vcfparser
from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.beacon import BeaconApi

LOG = logging.getLogger(__name__)

class UploadBeaconApi():

    def __init__(self, status: Store, hk_api: HousekeeperAPI, scout_api: ScoutAPI,
                 beacon_api: BeaconApi):
        self.status = status
        self.housekeeper = hk_api
        self.scout = scout_api
        self.beacon = beacon_api

    def upload(self, family_id: str, panel: list, dataset: str='clinicalgenomics', outfile: str=None, customer: str=None, qual: int=20, reference: str="grch37"):
        """Upload variants to Beacon for a family."""

        try:
            family_obj = self.status.family(family_id)
            # get the VCF file
            analysis_obj = family_obj.analyses[0]
            analysis_date = analysis_obj.started_at or analysis_obj.completed_at
            hk_version = self.housekeeper.version(family_id, analysis_date)
            hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-snv-clinical']).first()

            if hk_vcf is None:
                LOG.info("regular clinical VCF not found, trying old tag")
                hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-clinical-bin']).first()
                if hk_vcf is None:
                    LOG.error("Couldn't find any vcf file tag!")

            status_msg = None

            #retrieve samples contained in VCF file:
            vcf_samples = vcfparser.get_samples(hk_vcf.full_path.strip())

            # list affected samples
            affected_samples = [link_obj.sample for link_obj in family_obj.links if
                                link_obj.status == 'affected']
            sample_ids = [sample_obj.internal_id for sample_obj in affected_samples]

            # Process only samples contained in VCF file:
            sample_ids = [element for element in sample_ids if element in vcf_samples]

            if sample_ids:
                status_msg = str(dt.datetime.now())
                status_msg += "," + str(hk_vcf.full_path.strip()) + "," +qual

                path_to_panel = ''
                temp_panel = None

                # If one or more valid panels are supplied generate gene panel BED file
                used_panels = []
                if not panel[0] == 'None':
                    print('Generating variants filter based on ', len(panel), ' gene panels')
                    bed_lines = self.scout.export_panels(panel)
                    temp_panel = NamedTemporaryFile('w+t',suffix='_chiara.'+','.join(panel))
                    temp_panel.write('\n'.join(bed_lines))
                    path_to_panel = temp_panel.name

                    ## capture specifics for gene panels in order to record panels used in status db at the end of the upload operation.
                    n_panels = len(panel)
                    with open(temp_panel.name, "r") as panel_lines:
                        while n_panels:
                            for line in panel_lines:
                                if line.startswith("##gene_panel="): #header with specifics of 1 panel
                                    templine = (line.strip()).split(',')
                                    temp_panel_tuple = []
                                    for tuple_n in templine:

                                        #create a tuple with these fields from the panel: name, version, date:
                                        temp_panel_tuple.append(tuple_n.split('=')[1])

                                    #print(tuple(temp_panel_tuple))
                                    if not tuple(temp_panel_tuple) in used_panels:
                                        used_panels.append(tuple(temp_panel_tuple))
                                    n_panels -= 1

                    status_msg += "," + str(used_panels)

                else:
                    LOG.info("Panel was set to 'None', so all variants are going to be uploaded.")
                    path_to_panel = None
                    status_msg += str(path_to_panel)

                result = self.beacon.upload(
                    vcf_path = hk_vcf.full_path,
                    panel_path = path_to_panel,
                    dataset = dataset,
                    outfile = outfile,
                    customer = customer,
                    samples = sample_ids,
                    quality = qual,
                    genome_reference = reference,
                )

                if temp_panel:
                    temp_panel.close()

                #mark samples as uploaded to beacon
                for sample_obj in affected_samples:
                    if sample_obj.internal_id in sample_ids:

                        sample_obj.beaconized_at = status_msg
                        print("\n",str(sample_obj),"----->", sample_obj.beaconized_at)
                self.status.commit()

                return result

            else:
                return None

        except Exception as e:
            LOG.critical("cg/meta/upload/beacon.py. The following error occurred:%s", e)


    def remove_vars(self, item_type, item_id):
        """Remove beacon for a sample or one or more affected samples from a family."""

        LOG.info("I'm about to remove item: %s (%s)", item_id, item_type)

        try:

            # remove vars for all affected samples in a family:
            if item_type == 'family':
                family_obj = self.status.family(item_type)

                # list affected samples
                affected_samples = [link_obj.sample for link_obj in family_obj.links if
                                    link_obj.status == 'affected

                print(str(affected_samples))





            else: # remove vars for a single sample:
                print("remove vars for a single sample:",item_id)

            return 2

        except Exception as e:
            LOG.critical("cg/meta/upload/beacon.py. The following error occurred:%s", e)
