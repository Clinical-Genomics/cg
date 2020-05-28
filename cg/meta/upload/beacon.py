import ast
import logging
import datetime as dt
import os
import scout
import sys
import time
from tempfile import NamedTemporaryFile

from cgbeacon.utils import vcfparser
from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.beacon import BeaconApi

LOG = logging.getLogger(__name__)


class UploadBeaconApi:
    def __init__(
        self, status: Store, hk_api: HousekeeperAPI, scout_api: ScoutAPI, beacon_api: BeaconApi
    ):
        self.status = status
        self.housekeeper = hk_api
        self.scout = scout_api
        self.beacon = beacon_api

    def upload(
        self,
        family_id: str,
        panel: list,
        dataset: str = "clinicalgenomics",
        outfile: str = None,
        customer: str = None,
        qual: int = 20,
        reference: str = "grch37",
    ):
        """Upload variants to Beacon for a family."""

        family_obj = self.status.family(family_id)
        # get the VCF file
        analysis_obj = family_obj.analyses[0]
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(family_id, analysis_date)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=["vcf-snv-clinical"]).first()

        if hk_vcf is None:
            LOG.info("regular clinical VCF not found, trying old tag")
            hk_vcf = self.housekeeper.files(
                version=hk_version.id, tags=["vcf-clinical-bin"]
            ).first()

            if hk_vcf is None:
                LOG.error("Couldn't find any vcf file tag!")

        status_msg = None

        # retrieve samples contained in VCF file:
        vcf_samples = vcfparser.get_samples(hk_vcf.full_path.strip())

        # list affected samples
        affected_samples = [
            link_obj.sample for link_obj in family_obj.links if link_obj.status == "affected"
        ]
        affected_ids = [sample_obj.internal_id for sample_obj in affected_samples]

        # Process only samples contained in VCF file:
        sample_ids = [element for element in affected_ids if element in vcf_samples]

        if len(sample_ids) == 0:
            LOG.critical(
                "None of the affected samples for this family %a could be found among the samples in VCF file %s",
                affected_ids,
                vcf_samples,
            )
            sys.exit(1)

        if sample_ids:
            # Check if any of these samples are already in beacon. If they are raise error
            for sample in sample_ids:
                if (
                    self.status.sample(sample).beaconized_at
                    and len(self.status.sample(sample).beaconized_at) > 0
                ):
                    LOG.critical(
                        "It looks like sample %s is already in Beacon! If you want to re-import it you have to remove its variants first! --> (cg clean beacon %s -type sample).",
                        sample,
                        sample,
                    )
                    sys.exit(1)

            status_msg = str(dt.datetime.now())
            status_msg += "|" + str(hk_vcf.full_path.strip()) + "|" + str(qual)

            path_to_panel = ""
            temp_panel = None

            # If one or more valid panels are supplied generate gene panel BED file
            used_panels = []

            if panel[0] == "None":
                LOG.info("Panel was set to 'None', so all variants are going to be uploaded.")
                path_to_panel = None
                status_msg += "|" + str(path_to_panel)
            else:
                print("Generating variants filter based on ", len(panel), " gene panels")
                bed_lines = self.scout.export_panels(panel, None)
                temp_panel = NamedTemporaryFile("w+t", suffix="_chiara." + ",".join(panel))
                temp_panel.write("\n".join(bed_lines))
                path_to_panel = temp_panel.name

                ## capture specifics for gene panels in order to record panels used in status db at the end of the upload operation.
                n_panels = len(panel)
                with open(temp_panel.name, "r") as panel_lines:
                    while n_panels:
                        for line in panel_lines:
                            if line.startswith("##gene_panel="):  # header with specifics of 1 panel
                                templine = (line.strip()).split(",")
                                temp_panel_tuple = []
                                for tuple_n in templine:
                                    # create a tuple with these fields from the panel: name, version, date:
                                    temp_panel_tuple.append(tuple_n.split("=")[1])

                                # print(tuple(temp_panel_tuple))
                                if not tuple(temp_panel_tuple) in used_panels:
                                    used_panels.append(tuple(temp_panel_tuple))
                                    print("---->", tuple(temp_panel_tuple), sep="")
                                n_panels -= 1

                status_msg += "|" + str(used_panels)

            result = self.beacon.upload(
                vcf_path=hk_vcf.full_path,
                panel_path=path_to_panel,
                dataset=dataset,
                outfile=outfile,
                customer=customer,
                samples=sample_ids,
                quality=qual,
                genome_reference=reference,
            )

            if temp_panel:
                temp_panel.close()

            # mark samples as uploaded to beacon
            for sample_obj in affected_samples:
                if sample_obj.internal_id in sample_ids:

                    sample_obj.beaconized_at = status_msg
                    print("\n", str(sample_obj), "----->", sample_obj.beaconized_at)
            self.status.commit()

            return result

    def create_bed_panels(self, list_of_panels: list):
        """Creates a bed file with chr. coordinates from a list of tuples with gene panel info ('panel_id', 'version', date, 'Name')."""

        panel_names = [i[0] for i in list_of_panels]
        panel_versions = [float(i[1]) for i in list_of_panels]

        bed_lines = self.scout.export_panels(panel_names, panel_versions)
        temp_panel = NamedTemporaryFile("w+t", suffix="_gene_panel.bed")
        temp_panel.write("\n".join(bed_lines))

        ############# Additional check to verify that beacon upload and beacon clean use the same panels #############
        scout_panels = []
        with open(temp_panel.name, "r") as panel_lines:
            for line in panel_lines:
                if line.startswith("##gene_panel="):
                    templine = (line.strip()).split(",")
                    temp_panel_tuple = []
                    for tuple_n in templine:
                        # create a tuple with these fields from the panel: name, version, date:
                        temp_panel_tuple.append(tuple_n.split("=")[1])

                    # print(tuple(temp_panel_tuple))
                    if not tuple(temp_panel_tuple) in scout_panels:
                        scout_panels.append(tuple(temp_panel_tuple))
                        print("---->", tuple(temp_panel_tuple), sep="")

        # Do check that the panels in scout are still the same as when the variants were uploaded in beacon:
        if scout_panels.sort() == list_of_panels.sort():
            LOG.info("Panels retrieved in scout corespond to those used for beacon upload.")
            return temp_panel
        else:
            return None
        ##############################################################################################################

    def remove_vars(self, item_type, item_id):
        """Remove beacon for a sample or one or more affected samples from a family."""

        temp_panel = None

        if item_type == "family":  # remove vars for all affected samples in a family:
            LOG.info("Removing from beacon variants for family: %s", item_id)
            family_obj = self.status.family(item_id)

            # list affected samples
            samples_to_remove = [
                link_obj.sample
                for link_obj in family_obj.links
                if link_obj.status == "affected"
                if link_obj.sample.beaconized_at
            ]

            if samples_to_remove:
                # get the beacon upload info from the field "beaconized_at":
                for sample in samples_to_remove:

                    # check first if the subject is on beacon:
                    if sample.beaconized_at == "":
                        LOG.critical(
                            "Affected sample %s from family %s is affected but was not found in beacon!",
                            sample.internal_id,
                            item_id,
                        )
                        break

                    beacon_info = sample.beaconized_at.split("|")
                    print("sample:", sample.internal_id, "\t--->", str(beacon_info))

                    LOG.info("######## Processing sample %s ########", sample.internal_id)

                    # Chech that path to VCF file with vars that went into beacon exists and get samples contained in that VCF file:
                    vcf_samples = vcfparser.get_samples(beacon_info[1])
                    if sample.internal_id in vcf_samples:

                        if beacon_info[3] == "None":
                            LOG.warn(
                                "No panel was associated to this beacon upload. Removing all variants for this sample."
                            )

                            results = self.beacon.remove_vars(
                                sample.internal_id, beacon_info[1], None, int(beacon_info[2])
                            )

                            LOG.info(
                                "Variants removed for sample %s: %s", sample.internal_id, results
                            )

                            if results:
                                sample.beaconized_at = ""
                                self.status.commit()
                        else:
                            # If gene panels were used, retrieve them into a bed file:
                            panel_list = list(ast.literal_eval(beacon_info[3]))

                            # Create bed file with chr. intervals from panels:
                            temp_panel = self.create_bed_panels(panel_list)

                            if temp_panel:
                                LOG.info(
                                    "passing ID, VCF file and gene panels file to beacon handler"
                                )

                                results = self.beacon.remove_vars(
                                    sample.internal_id,
                                    beacon_info[1],
                                    temp_panel.name,
                                    int(beacon_info[2]),
                                )
                                temp_panel.close()

                                LOG.info(
                                    "Variants removed for sample %s: %s",
                                    sample.internal_id,
                                    results,
                                )
                                if results:
                                    sample.beaconized_at = ""
                                    self.status.commit()
                            else:
                                LOG.critical(
                                    "Current scout panels don't match with those used for the variant upload! Automatic variant removal is not possible."
                                )

                    else:
                        LOG.warn(
                            "sample %s is not contained in the annotated vcf file, skipping it!",
                            sample.internal_id,
                        )
            else:
                LOG.warn("Could't find any affected sample in beacon for family %s!", item_id)

        else:  # remove vars for a single sample:
            LOG.info("Removing from beacon variants for sample: %s", item_id)
            sample_obj = self.status.sample(item_id)

            if sample_obj:
                beacon_info = sample_obj.beaconized_at.split("|")
                LOG.info("######## Processing sample %s ########", sample_obj.internal_id)
                print("info:", beacon_info)

                # Chech that path to VCF file with vars that went into beacon exists and get samples contained in that VCF file:
                vcf_samples = vcfparser.get_samples(beacon_info[1])
                if sample_obj.internal_id in vcf_samples:

                    if not beacon_info[3] == "None":
                        panel_list = list(ast.literal_eval(beacon_info[3]))

                        # Create bed file with chr. intervals from panels:
                        temp_panel = self.create_bed_panels(panel_list)

                        if temp_panel:

                            LOG.info("passing ID, VCF file and gene panels file to beacon handler")
                            results = self.beacon.remove_vars(
                                sample_obj.internal_id,
                                beacon_info[1],
                                temp_panel.name,
                                int(beacon_info[2]),
                            )
                            temp_panel.close()

                            LOG.info(
                                "Variants removed for sample %s: %s",
                                sample_obj.internal_id,
                                results,
                            )

                            if results:
                                sample_obj.beaconized_at = ""
                                self.status.commit()

                        else:
                            LOG.critical(
                                "Current scout panels don't match with those used for the variant upload! Automatic variant removal is not possible."
                            )
                    else:
                        LOG.warn(
                            "No panel was associated to this beacon upload. Removing all variants for this sample."
                        )

                        results = self.beacon.remove_vars(
                            sample_obj.internal_id, beacon_info[1], None, int(beacon_info[2])
                        )

                        LOG.info(
                            "Variants removed for sample %s: %s", sample_obj.internal_id, results
                        )

                        if results:
                            sample_obj.beaconized_at = ""
                            self.status.commit()

                else:
                    LOG.warn(
                        "sample %s is not contained in the annotated vcf file!",
                        sample_obj.internal_id,
                    )
            else:
                LOG.critical("Couldn't find a sample named '%s' in cg database!", item_id)
