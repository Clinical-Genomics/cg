# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.0.0/)

## [85.6.1] - 2026-04-17
### Fixed
- Fix #5028 and a few similar ones by adding an extra trailing newline (#5029)

## [85.6.0] - 2026-04-17
### Added
- Data set parameter parsed from the statina section of CGConfig. Used when uploading to statina. (#5009)
### Changed
- Removed the external ref flag from Fluffy start and run (#5009)
- Added batch ref flag to Fluffy start and run (#5009)

## [85.5.0] - 2026-04-16
### Added
- Method `get_input_amount`in the LIMS API that return the latest input amount for a DNA sample (#5011)
- Input amount step names and udf keys in constants (#5011)
### Changed
- Order of columns in the "provberedning" section of the delivery report (#5011)

## [85.4.1] - 2026-04-16
### Fixed
- README badge for CI - tests and coverage

## [85.4.0] - 2026-04-16
### Added
- A PATCH endpoint called `samples`, which allows you to update the `lims_status` for a list of samples. (#5030)

## [85.3.3] - 2026-04-16
### Fixed
- Lims_status type hinted as LimsStatus (#5027)

## [85.3.2] - 2026-04-15
### Fixed
- Enum handling for lims_status (#5025)

## [85.3.1] - 2026-04-15
### Added
- Lims_status to Sample table (#5023)

## [85.3.0] - 2026-04-14
### Added
- RawDataUploadAPI — new upload API class following the same pattern as other workflow upload APIs (#4965)
- Deliver_raw_data module (cg/services/deliver_files/deliver_raw_data.py) — shared deliver_analyses function that delivers files and updates upload_started_at in StatusDB (#4965)
### Fixed
- Cg upload <case_id> — now routes RAW_DATA workflow cases through RawDataUploadAPI instead of falling through unhandled (#4965)

## [85.2.2] - 2026-04-13
### Changed
- Switched from AZ to AG as contact person in invoicing templates (#5019)

## [85.2.1] - 2026-04-09
### Changed
- Balsamic v19 (#4915)

## [85.2.0] - 2026-04-09
### Added
- Field `pipeline_deliverables` to every nextflow pipeline config (#4991)
- In the NFAnalysisAPI and its children, (#4991)
### Changed
- In the NFAnalysisAPI and its children, remove the method `get_bundle_filenames_path`. Instead, we use the `pipeline_deliverables` parsed from the CGConfig. (#4991)

## [85.1.6] - 2026-04-01
### Changed
- Add support in the `/deliver` endpoint to parse the authentication token of the user (in CiGRID) that calls the endpoint. (#4976)
- The mark as delivered service now forwards the authentication token from the endpoint to the Trailblazer API (#4976)
- The Trailblazer API now builds a header with the section `"X-On-Behalf-Of"` if given an authentication token to use in the request towards Trailblazer (#4976)

## [85.1.5] - 2026-04-01
### Changed
- An analysis failing its analysis QC does no longer raise a click abort. (#4989)

## [85.1.4] - 2026-03-31
### Added
- Trailblazer notification for on-instrument demultiplexed NovaSeqX runs, so they are tracked in Trailblazer with the DEMULTIPLEX workflow and immediately marked as COMPLETED (#4901)
- Analysis manifest parsing in is_syncing_complete — files listed in Analysis/<version>/Manifest.tsv are now included in the sync verification, preventing sync from being confirmed before demultiplexed data has landed (#4901)
### Changed
- Renamed CLI function `copy-completed-sequencing-runs` to `link-onboard-demultiplexing` (#4901)
- Copy_run_dir_to_tmp now uses rsync with --exclude=Analysis instead of cp -r, so the Analysis/ directory is excluded from backup encryption (#4901)
- Create_all_sheets now skips creating a sample sheet if demultiplexing was done onboard (#4901)
- Link_onboard_demultiplexed_flow_cells now adds the used samplesheet to housekeeper (#4901)
### Fixed
- Has_demultiplexing_started_on_sequencer now checks the sequencing-runs/ directory instead of demultiplexed-runs/, so on-instrument demultiplexing is correctly detected before data has been copied (#4901)

## [85.1.3] - 2026-03-31
### Changed
- Make the `mark_analyses_as_delivered` method from the `TrailblazerAPI` return the analyses from the Trailblazer reponse (#4988)
- Make the `mark_analyses` method from the `MarkAsDeliveredService` propagate the return value from the TrailblazerAPI method (#4988)
- Make the endpoint return a Flask response with the analyses coming from Trailblazer if successful., and provide a message in the HTTP response if fails (#4988)

## [85.1.2] - 2026-03-31
### Added
- Add valid types for should-deliver-sample (#4983)

## [85.1.1] - 2026-03-31
### Added
- New sets of indexes (#4984)
### Changed
- Excel orderform fixture (#4984)
- Version of the orderform (#4984)

## [85.1.0] - 2026-03-30
### Changed
- New RNAFusion samples are always persisted with `is_tumour=True`. (#4964)
- New RNAFusion samples set as normal samples in the excel order form show a warning that they will be persisted as tumour samples. (#4964)
- Existing samples in an RNAFusionOrder fail validation if they are normal samples. (#4964)

## [85.0.2] - 2026-03-26
### Fixed
- Removed the FREEMIX qc check for raredisease WES cases. (#4975)

## [85.0.1] - 2026-03-26
### Fixed
- Negative controls do not have their reads checked in when delivering an analysis (#4980)

## [85.0.0] - 2026-03-26
### Changed
- New samples get their case_sample entries' should_deliver_sample set to true. (#4970)

## [84.9.3] - 2026-03-26
### Fixed
- Removed files that should not be stored. (#4978)
- Patched the path to the index file. (#4978)

## [84.9.2] - 2026-03-25
### Added
- Generics for both the type of case and sample in the ordering flow to get better typing. (#4967)

## [84.9.1] - 2026-03-23
### Added
- Information in delivery report which columns have information originating from customer (#4961)

## [84.9.0] - 2026-03-23
### Added
- Alembic migration with new column `should_deliver_sample` for CaseSample table and making `trailblazer_id` an indexed column. (#4955)
- Endpoint `deliver` that receives the jsonified trailblazer ids for the analyses to deliver (#4955)
- `MarkAsDeliveredService` that determines which samples should be updated and calls trailblazer for a given analysis (#4955)
- CRUD strict function to get an analysis from a trailblazer id (#4955)
- Tests (#4955)

## [84.8.0] - 2026-03-19
### Changed
- Remove code pertaining to encryption, archiving and fetching of spring files to/from PDC (#4952)

## [84.7.2] - 2026-03-18
### Fixed
- Reference the cgh file using the sample name in the Raredisease Deliverables file (#4959)

## [84.7.1] - 2026-03-13
### Changed
- The order of the upload commands for Nallo. Specifically, put `upload_coverage` before `generate_delivery_report`. Follows the same order as MIP-DNA (#4953)

## [84.7.0] - 2026-03-12
### Changed
- Balsamic-UMI uses the AnalysisStarter (#4912)

## [84.6.0] - 2026-03-12
### Added
- `chanjo_38` config field in `CGConfig` and `ChanjoConfig` model to support a separate chanjo instance for hg38 (#4931)
- `chanjo_api_for_genome_build()` factory in `cg/apps/coverage/chanjo_api.py` (#4931)
- `--genome-version` flag (`hg19`/`hg38`) on `cg upload coverage` and `cg upload validate` to allow manual selection of chanjo instance (#4931)
- Chanjo1 (hg38) upload step in `NalloUploadAPI.upload()` (#4931)
### Changed
- `NalloAnalysisAPI.get_sample_coverage()` switched from Chanjo2 to Chanjo1 (hg38 instance) (#4931)
- `RarediseaseAnalysisAPI` and `NalloAnalysisAPI` now set `self.chanjo_api` in their constructors via `chanjo_api_for_genome_build` and `WORKFLOW_TO_GENOME_VERSION_MAP` (#4931)
- `cg upload coverage` and `cg upload validate` now instantiate `ChanjoAPI` directly rather than via the `CGConfig.chanjo_api` property (#4931)

## [84.5.4] - 2026-03-11
### Added
- Validation that source_comment is mandatory when source is set to other. (#4949)

## [84.5.3] - 2026-03-11
### Fixed
- The parsing of the MultiQC per sample for raredisease, to parse `multiqc_picard_AlignmentSummaryMetrics` from the `report_saved_raw_data` section. (#4947)
- The `RarediseaseQCMetrics` model now accepts the picard metrics instead of the qualimap metrics (#4947)
- The delivery report now uses the percentage of reads aligned from `multiqc_picard_AlignmentSummaryMetrics` instead of calculating it using metrics from qualimap (#4947)
- Remove qualimap entriews for raredisease multiqc and metrics deliverables fixtures (#4947)

## [84.5.2] - 2026-03-10
### Added
- New source `buffer` added (#4943)
### Changed
- Version 36 is the accepted version of order form 1508 (#4943)

## [84.5.1] - 2026-03-09
### Added
- `DSD`, `DSD-S`, `POI`, `OPHTHALMO`, `ANTE-ED`, `SED`, and `ALBINISM` panels to `GenePanelMasterList` (#4938)
### Changed
- Removed `GenePanelCombo` class and all combo expansion logic as it would not be used anymore (#4938)

## [84.5.0] - 2026-03-09
### Changed
- Remove _pe suffix from taxprofiler deliverables. (#4839)

## [84.4.8] - 2026-03-04
### Added
- An A (#4932)

## [84.4.7] - 2026-03-03
### Changed
- F"SPRING to FASTQ decompression has not completed or was never started for {sample.internal_id}" (#4930)

## [84.4.6] - 2026-03-03
### Added
- App-tag-specific QC metric conditions for RNAfusion, so that depletion samples (RNAWDPR100) get appropriate thresholds (#4928)
- Application_tag property on Sample as a shortcut for sample.application_version.application.tag (#4928)
### Changed
- More descriptive names, `metric_id` -> `sample_id` and `get_workflow_metrics` -> `get_qc_conditions_for_workflow` (#4928)

## [84.4.5] - 2026-03-02
### Added
- New master step names for the RNA depletion workflow in LIMS (#4923)

## [84.4.4] - 2026-02-26
### Fixed
- The source_comment is sent to LIMS as source when source=other. (#4924)

## [84.4.3] - 2026-02-26
### Added
- Field `cache_version` to the cg config for balsamic. (#4911)

## [84.4.2] - 2026-02-26
### Changed
- We send one request for all the files that we want to archive instead of one request per file. (#4908)

## [84.4.1] - 2026-02-26
### Changed
- Remove coveralls (#4925)

## [84.4.0] - 2026-02-25
### Added
- Upload to gens command added to to nallo uploads (#4913)
- In `gens` command, set `hg38` as `--genome-build` when the workflow is Nallo (#4913)
- Test for happy path of `upload` method in the `NalloUploadAPI` (#4913)
### Changed
- Updated test for `gens` command (#4913)
- Renamed `NalloUploadAPI` module to match the name of the class (#4913)

## [84.3.2] - 2026-02-24
### Added
- Sambamba output file to the deliverables of nallo (#4843)

## [84.3.1] - 2026-02-23
### Added
- Save GENS files from Nallo (#4868)
### Changed
- WhatHap stats blocks file name (#4868)

## [84.3.0] - 2026-02-19
### Changed
- Samples with a delivery_at in the following workflows will pass on enough reads, regardless of the amount: (#4906)
- BALSAMIC (#4906)
- BALSAMIC_PON (#4906)
- BALSAMIC_UMI (#4906)
- MIP_DNA (#4906)
- MIP_RNA (#4906)
- RAREDISEASE (#4906)
- RNAFUSION (#4906)
- TOMTE (#4906)
- NALLO (#4906)
- RAW_DATA (#4906)

## [84.2.1] - 2026-02-18
### Fixed
- Revert "Auto pass on sample with delivered_at date (#4895)" (#4905)

## [84.2.0] - 2026-02-18
### Changed
- Samples with a delivery_at in the following workflows will pass on enough reads, regardless of the amount: (#4895)
- BALSAMIC (#4895)
- BALSAMIC_PON (#4895)
- BALSAMIC_UMI (#4895)
- MIP_DNA (#4895)
- MIP_RNA (#4895)
- RAREDISEASE (#4895)
- RNAFUSION (#4895)
- TOMTE (#4895)
- NALLO (#4895)
- RAW_DATA (#4895)

## [84.1.1] - 2026-02-18
### Fixed
- Added RD to the list of workflows with scout upload. (#4899)

## [84.1.0] - 2026-02-16
### Added
- Validation rule preventing samples not related to other samples in the same case in RD and MIP-DNA orders. (#4874)

## [84.0.9] - 2026-02-16
### Added
- The CHD gene panel to the clinical master list (#4893)

## [84.0.8] - 2026-02-16
### Added
- Comma separation for large numbers on `Reads` in `Sample` table in the Admin view: (#4877)
- SI prefix on `Hifi Yield` in the `Sample` table in the Admin view : (#4877)

## [84.0.7] - 2026-02-16
### Added
- Cg now calls the mutacc-auto extract command with the --conda flag (#4884)

## [84.0.6] - 2026-02-16
### Changed
- The version of black in the pre-commit-config (#4890)

## [84.0.5] - 2026-02-11
### Fixed
- Refactor bed methods into StoreHelpers (#4880)

## [84.0.4] - 2026-02-10
### Added
- Integration test for the command `cg workflow post-process all` when there is data for one PacBio sequencing run to process. (#4864)
- Added required contents to `.transferdone` file (#4864)
- Updated zip file with barcodes report (#4864)
- New xml file with metadata to be parsed by the post processing flow (#4864)
### Changed
- Integration tests for workflows moved to folder `integration/workflows` (#4864)

## [84.0.3] - 2026-02-09
### Changed
- Made the filter function in the readhandler that gets the bed version using a short name, also filters with genome version. (#4875)
- This new function is used at the start of MIP, RareDisease and Balsamic. And in the Loqusdb upload of Balsamic. (#4875)

## [84.0.2] - 2026-02-05
### Changed
- No metadata is sent when archiving files at K. (#4842)

## [84.0.1] - 2026-02-04
### Changed
- Genome version on BedVersion table is not nullable (#4873)
- Genome version on BedVersion table is now an enum allowing hg19, hg38 and cfam3 (#4873)
- Unique constraint added on the BedVersion table for the combination of shortname, version and genome version (#4873)

## [84.0.0] - 2026-02-04
### Added
- Response from `/api/v1/pacbio_sequencing_runs` includes two new fields: `run_id` and `unique_id` their values corresponds to the fields of the same name in Pacbio SmrtLink and the existing field `run_name` now holds the custom name set for the run in Pacbio (#4865)
### Changed
- Renamed fields in response from `/api/v1/pacbio_smrt_cell_metrics` so that `runs` -> `metrics` and `run_name` -> `run_id` (#4865)

## [83.20.3] - 2026-02-04
### Changed
- Revert external samples from being handled in the automatic sequencing qc (#4854)

## [83.20.2] - 2026-02-03
### Added
- Test coverage (#4854)
### Fixed
- Patched the check in func `sample_has_enough_hifi_yield` (#4854)

## [83.20.1] - 2026-02-03
### Added
- Run name is now visible in the SMRT cell metrics admin view (#4867)

## [83.20.0] - 2026-02-03
### Changed
- Made run_name, run_id and unique_id non-nullable for the table pacbio_sequencing_run (#4866)

## [83.19.1] - 2026-02-03
### Added
- Test coverage for raredisease_config_builder (#4820)
### Changed
- Removed the d4 file tag from RAREDISEASE_SAMPLE_TAGS and the d4_file model attribute from ScoutRarediseaseIndividual. (#4820)
- Removed fetching of the d4 file in raredisease_config_builder. (#4820)

## [83.19.0] - 2026-02-02
### Added
- Support in the metrics parser to parse the Pacbio run metadata XML file. (#4860)
- Pydantic objects to extract `run_name` and `unique_id` from the XML file. (#4860)
- Dummy metadata file for the fixture (#4860)
### Changed
- The PacbioSequencingRunDTO to include `run_name` and `unique_id` (#4860)
- The Pacbio Store service to persist the `run_name` and `unique_id` from the DTO to the PacbioSequenicngRun table in StatusDB (#4860)
- The Pacbio Housekeeper Store service to save the `metadata.xml` file to the smrt cell bundle with tag `smrt-link-metadata`. (#4860)

## [83.18.2] - 2026-01-29
### Fixed
- We now run black 26.1.0 (#4856)

## [83.18.1] - 2026-01-29
### Added
- Raredisease: add verifybamid2 QC contamination check (#4863)

## [83.18.0] - 2026-01-28
### Changed
- Https://github.com/Clinical-Genomics/cg/blob/d54d78368408e2a3e2254e7b7adc836f6474b80e/cg/meta/workflow/raredisease.py#L148 (#4824)

## [83.17.1] - 2026-01-28
### Added
- Methbat output to Nallo bundle (#4852)
### Changed
- Modkit tags (#4852)

## [83.17.0] - 2026-01-28
### Added
- Add columns `Unique ID` and `Run Name` to the PacbioSequencingRun table (#4850)
### Changed
- Rename the existing column `Run Name` to `Run ID`. (#4850)
- Rename all variables in the code that made reference to the old `run_name` into `run_id`. (#4850)

## [83.16.4] - 2026-01-27
### Changed
- The HiFi yield is showed in Gb for a sample (#4857)

## [83.16.3] - 2026-01-27
### Changed
- Removed `link` and `resolve_compression` from the list of commands of MIP-DNA (#4809)
- Removed unused Nextflow constants (#4809)
- Remove `compute_env_base` and `nextflow_binary_path` attributes of the NFAnalysisAPIs (#4809)
- Remove unused methods from NfAnalysisAPI (#4809)
- Remove `compute_env` from NF config classes in cg_config (#4809)

## [83.16.2] - 2026-01-22
### Changed
- Some INFO logs to DEBUG (#4851)

## [83.16.1] - 2026-01-20
### Fixed
- The CompressAPI gets a SpringBackupAPI injected in the AnalysisStarterFactory (#4845)

## [83.16.0] - 2026-01-20
### Added
- `device_type` property in sample (#4838)
- `hifi_yield` and `uses_reads` (discriminator) attributes to the dict representation of `Sample` (#4838)
- Tests (#4838)

## [83.15.4] - 2026-01-20
### Changed
- The `cg init` command no longer exists. (#4840)

## [83.15.3] - 2026-01-19
### Added
- Checker method in AnalysisStarter (#4822)
- New Exception (#4822)
### Fixed
- Fix affected tests (#4822)

## [83.15.2] - 2026-01-19
### Changed
- BalsamicConfigurator.configure raises a MultipleCaptureKitsError when multiple different capture kits are found in Lims for the provided case (#4823)

## [83.15.1] - 2026-01-19
### Changed
- Instead of exiting early when a qc check raises an exception, continue running checks for the rest of the cases but exit the cli command with a fail exit code. (#4832)

## [83.15.0] - 2026-01-19
### Added
- Utils functions for raw data sequencing qc (#4831)
- Add qc checks for yield based cases (#4831)
### Changed
- Fastq raw data QC uses expected reads, not "any sample has reads" (#4831)

## [83.14.0] - 2026-01-15
### Added
- Function `case_pass_sequencing_qc_on_hifi_yield` to be used for Nallo cases (#4821)
- Functions to evaluate sequencing qc on yield for express samples. (#4821)
### Changed
- Renamed function using reads to include the suffix `on_reads` (#4821)
- Implemented some functionality as properties in the Store models instead of utils methods (#4821)

## [83.13.3] - 2026-01-14
### Added
- Add deploy-cg-hasta2-login workflow (#4826)

## [83.13.2] - 2026-01-13
### Fixed
- Editing an entry in the Application table works without setting any order types. (#4818)

## [83.13.1] - 2026-01-13
### Added
- Add Noonan panel - Fix #4804 (#4815)

## [83.13.0] - 2026-01-13
### Added
- Property in the `Sample` database model `hifi_yield` that calculates hifi yield for samples with Pacbio sample sequencing runs, and return None for others. (#4817)

## [83.12.0] - 2026-01-12
### Added
- Target_hifi_yield to the Application table (optional BigInt) (#4816)
- Percent_hifi_yield_guaranteed to the Application table (optional integer) (#4816)
- Show the columns in admin view (#4816)

## [83.11.8] - 2026-01-12
### Changed
- Renamed new endpoint in `cg/server/endpoints/sequencing_run/pacbio_sequencing_run.py` (#4812)
- Remove endpoint `pacbio_sequencing_run/<run_name` (#4812)
- Remove Blueprint `PACBIO_SEQUENCING_RUN_BLUEPRINT` (#4812)

## [83.11.7] - 2026-01-12
### Added
- Alembic migration to add foreign key columns and populate new columns (#4808)
### Changed
- Admin view displays the same information as before (#4808)
- Post processing of pacbio runs sets up this relationship (#4808)

## [83.11.6] - 2026-01-12
### Changed
- Change line ending from CRLF -> LF (#4810)

## [83.11.5] - 2026-01-12
### Added
- COMDP to GenePanelMasterList StrEnum (#4811)

## [83.11.4] - 2026-01-09
### Changed
- Fixes #4776 (#4796)

## [83.11.3] - 2026-01-09
### Added
- Chromograph coverage and autozygous images are now uploaded to scout (#4803)

## [83.11.2] - 2026-01-09
### Added
- Stored chromograph images for Nallo (#4751)
- Stored Sawfish VCFs for Nallo (#4751)
### Changed
- Name changes for already existing files with Nallo 0.9.1 (#4751)
### Fixed
- Nallo cases stores and uploads wrong version of repeat-file to Scout/Reviewer (#4751)

## [83.11.1] - 2026-01-08
### Fixed
- Flag handling is safer for refactored workflows (#4771)

## [83.11.0] - 2026-01-08
### Added
- Option to the `cg upload process-solved` command specifying which scout instance to use. (#4800)

## [83.10.0] - 2026-01-08
### Added
- The ID to the response for the endpoint called: "pacbio_sequencing_runs" (#4807)

## [83.9.0] - 2026-01-08
### Added
- PATCH Endpoint `/pacbio_sequencing_runs/<id>` to modify the comment or processed status of a pacbio sequencing run (#4805)

## [83.8.2] - 2026-01-07
### Changed
- Moved TomteParameters class to the AnalysisStarter module (#4780)
- Removed old code for nextflow config file creation (#4780)
- Removed old code for nextflow sample sheet creation (#4780)
- Removed old code for nextflow params file creator (#4780)

## [83.8.1] - 2026-01-07
### Changed
- Replace Peddy with Somalier in the Scout upload (#4791)

## [83.8.0] - 2026-01-07
### Changed
- Endpoint to return all pacbio sequencing runs (#4795)

## [83.7.1] - 2025-12-22
### Changed
- Docstrings for all pipelines, ensuring a consistent structure. (#4774)

## [83.7.0] - 2025-12-22
### Added
- Adds the creation of a PacBio sequencing run the Pacbio post-processing (#4789)
### Changed
- Renamed instances of `pacbio_sequencing_run` to `pacbio_smrt_cell_metrics` (#4789)

## [83.6.2] - 2025-12-22
### Fixed
- Replaced "Inherited cancer" in the panel master list, with the new abbreviation (#4792)

## [83.6.1] - 2025-12-18
### Added
- Add sensitive info warning to templates (#4756)

## [83.6.0] - 2025-12-18
### Added
- New endpoint /api/v1/pacbio_smrt_cell_metrics/<run_name> which gets the same data as /api/v1/pacbio_sequencing_run/<run_name>. (#4790)

## [83.5.0] - 2025-12-17
### Added
- Storage of four more taxprofiler files (#4785)

## [83.4.0] - 2025-12-17
### Added
- Table `pacbio_sequencing_run` (#4788)

## [83.3.0] - 2025-12-17
### Added
- Alembic migration (#4784)
### Changed
- Name of the table and the SQLAlchemy class (#4784)

## [83.2.4] - 2025-12-17
### Added
- Three new index sets (#4783)
- Expanded on one existing set (#4783)
### Changed
- Updated the current accepted orderform for RML (#4783)

## [83.2.3] - 2025-12-16
### Changed
- `config_path` will be empty in the POST request to the Trailblazer endpoint `/add-pending-analysis` for Nextflow pipelines. (#4733)

## [83.2.2] - 2025-12-15
### Changed
- Rewrite microsalt tests (#4772)

## [83.2.1] - 2025-12-11
### Fixed
- Fix flow cell retrieval handling incorrect sequencing run path (#4747)

## [83.2.0] - 2025-12-11
### Added
- Upload to Chanjo1 for raredisease analyses (#4768)
### Changed
- Filter on housekeeper tags `sambamba-depth` and `chanjo` when getting the coverage file (#4768)

## [83.1.2] - 2025-12-10
### Added
- Deepvariant reports to the housekeeper bundle for the raredisease pipeline (#4734)

## [83.1.1] - 2025-12-10
### Added
- Sambamba output file to the deliverables of raredisease (#4759)

## [83.1.0] - 2025-12-10
### Added
- The values under `report_saved_raw_data > multiqc_somalier` (in file multiqc_data.json) are made available for the delivery report generation. The keys from that dictionary are all prefixed with `somalier_` to avoid clashes with other keys. (#4752)
- Test coverage for the delivery report generated by `Nallo`. (#4752)
### Changed
- The somalier `sex` is used instead of peddy `predicted_sex` for the metric "Kön" under the heading "kvalitetsmått" in the delivery report. (#4752)

## [83.0.0] - 2025-12-10
### Changed
- Remove `dev` prefix from Tomte CLI commands and remove the call to start, config-case, run and start-available (#4754)
- Remove Old tests and fixtures (#4754)

## [82.0.7] - 2025-12-09
### Changed
- Rename function `is_sample_source_type_ffpe` to `is_sample_source_not_ffpe` (#4765)

## [82.0.6] - 2025-12-08
### Fixed
- Reads is non-nullable (#4728)
- Samples with null reads are set to 0. (#4728)

## [82.0.5] - 2025-12-08
### Changed
- File names for the files that contain sample sheet creators. (#4766)

## [82.0.4] - 2025-12-08
### Fixed
- Reads are updated rather than incremented for Pacbio samples. (#4748)

## [82.0.3] - 2025-12-08
### Changed
- Replaced SuSy with Freshdesk in delivery report

## [82.0.2] - 2025-12-08
### Fixed
- Decompress_case now correctly iterates through all samples (#4760)

## [82.0.1] - 2025-12-03
### Fixed
- Patch base command (#4753)

## [82.0.0] - 2025-12-02
### Changed
- Make the dev commands the production commands for raredisease (#4737)
- Update tests to use prod commands instead of dev commands (#4737)
- Remove commands managed variants and gene panels (#4737)
- Remove old tests (#4737)

## [81.0.0] - 2025-12-02
### Changed
- Commands swapped for dev commands for Nallo. (#4736)

## [80.1.1] - 2025-12-02
### Added
- New sequencing master step name for the Revio workflow in LIMS (#4749)

## [80.1.0] - 2025-12-01
### Added
- Cg workflow tomte dev-config-case (#4739)
- Cg workflow tomte dev-run (#4739)
- Cg workflow tomte dev-start (#4739)
- Cg workflow tomte dev-start-available (#4739)
- Tomte integrated into the AnalysisStarter (#4739)

## [80.0.3] - 2025-11-27
### Added
- Run (#4742)
- Config (#4742)
- Start (#4742)
- Start-available (#4742)

## [80.0.2] - 2025-11-26
### Changed
- Integration test for Nallo dev-start-available (#4718)

## [80.0.1] - 2025-11-25
### Changed
- Reset a case's action when HTTPErrors and SeqeraErrors are raised (#4735)

## [80.0.0] - 2025-11-25
### Added
- The optional flag `--resume` that can be set to either `true` or `false` to indicate if an analysis should be resumed or not. Defaults to `true` (#4712)
### Changed
- `run` now resumes the previous analysis by default (#4712)

## [79.1.0] - 2025-11-25
### Added
- Fetch phase_blocks and mt_bam paths and add to the Nallo scout load config (#4730)

## [79.0.0] - 2025-11-25
### Changed
- Deleted old commands and options (#4732)
- Deleted tests for old commands (#4732)
- Renamed dev commands (#4732)

## [78.5.0] - 2025-11-25
### Added
- Filtering based on ordered_at date. (#4665)
- An option to the `cg transfer lims` command that lets the user specify an age cutoff. If a sample was ordered before this cutoff, it will be filtered out and no request for that sample will be sent to LIMS. (#4665)

## [78.4.3] - 2025-11-24
### Added
- Add ticket hyperlinks to StatusDB (#4708)

## [78.4.2] - 2025-11-20
### Changed
- Cache TB Auth tokens & re-use until expired (#4722)

## [78.4.1] - 2025-11-20
### Changed
- All samples are valued equally in microSALT's qc checks, instead of certain app tags being deemed more urgent. (#4720)

## [78.4.0] - 2025-11-19
### Added
- Nallo dev-run (#4727)
- Nallo dev-start (#4727)
- Raredisease dev-run (#4727)
- Raredisease dev-start (#4727)
- RNAFUSION run (#4727)
- RNAFUSION dev-start (#4727)
- Taxprofiler run (#4727)
- Taxprofiler start (#4727)

## [78.3.5] - 2025-11-19
### Changed
- Raredisease delivery report changed percent_duplicates to percent_duplication (#4726)

## [78.3.4] - 2025-11-19
### Added
- Configurator (#4524)
- Tracker (#4524)
- ConfigFileCreator (#4524)
- Data classes (#4524)
### Changed
- The structure of the BalsamicConfig in the CGConfig (#4524)

## [78.3.3] - 2025-11-18
### Added
- Session_id column to Analysis (#4721)

## [78.3.2] - 2025-11-17
### Added
- Integration test for running nallo start-available with one available case to run (#4700)
- Utility method to create samples with bam files for integration tests (#4700)
### Changed
- Reworked mocking running processes so that a fixture `mocked_commands_and_outputs` can be provided where a given command will result in the specified output (#4700)
- Removed old logic where the display message was generated based on app tag, the message is now the one previously only used for MWR. (#4715)
### Fixed
- This will fix the issue where the "Copy delivery message" resulted in an error for Microsalt cases. (#4715)

## [78.3.1] - 2025-11-11
### Fixed
- Filter on case_id as well to get the correct STR file into the delivery report for Raredisease. (#4701)

## [78.3.0] - 2025-11-11
### Added
- Support for new flags (#4453)
- Loqusdb dumps for Panel analyses (#4453)
- Loqusdb dump fro WGS (#4453)
- Headjobs (#4453)
- Workflow-dir (#4453)
- Support for delivery report (#4453)
- Add Predicted sex to delivery report (#4453)
- Make sure that mean target coverage is rendered for WGS (#4453)
### Changed
- Allow for unknown gender (#4453)
- Removed flags `--benchmark` and `--mail-user` (#4453)

## [78.2.3] - 2025-11-11
### Fixed
- Log message typo (#4625)

## [78.2.2] - 2025-11-11
### Changed
- Pacbio_sequencing_run relationship renamed to override instrument_run (#4697)
- The pacbio_sequencing_run relationship back_populates sample_metrics (#4697)

## [78.2.1] - 2025-11-10
### Fixed
- Use non-strict version of lims capture kit (#4699)
- Use default value of `""` if capture kit returns None (#4699)

## [78.2.0] - 2025-11-10
### Added
- Sample sheet creator (#4674)
- Params file creator (#4674)
- Tracker (#4674)
- Nallo to AnalysisStarterFactory and ConfiguratorFactory (#4674)
- Dev commands (config-case, run, start, start-available) (#4674)
- SampleSheetCreator protocol (#4674)

## [78.1.1] - 2025-11-10
### Added
- Test for qc metrics. (#4695)
### Fixed
- Number for ribosomal_bases in the delivery report. (#4695)

## [78.1.0] - 2025-11-06
### Added
- Render the run name and plate in the Pacbio sample sequencing metrics admin view (#4542)
- Filter on the run name and plate in the Pacbio sample sequencing metrics admin view (#4542)

## [78.0.7] - 2025-11-05
### Changed
- Removed peddy sex check from Nallo delivery QC (#4685)

## [78.0.6] - 2025-11-05
### Added
- Changed get_active_applications_by_prep_category to get_applications_by_prep_category. (#4687)
### Changed
- Removed filtering of archived applications. (#4687)

## [78.0.5] - 2025-10-29
### Changed
- Bumped microSALT order form version (#4653)
- Bumped microbial fastq order form version (#4653)
- Removed parsing of extraction method for microSALT (#4653)

## [78.0.4] - 2025-10-28
### Added
- Phase blocks to Nallo bundle (#4671)

## [78.0.3] - 2025-10-23
### Added
- Two integration tests that runs the cg command `workflow balsamic start-available` with one case each ready to start. Two different cases are tested, the first one is a TGS case with a single tumor sample, the other a WGS case with two samples. (#4643)
- All necessary cli commands and http requests are made (#4643)
- All files are created in the correct place (#4643)

## [78.0.2] - 2025-10-23
### Changed
- Shortname is a non-nullable field on bed_version (#4666)

## [78.0.1] - 2025-10-21
### Fixed
- Removed aliases from the MIP-DNA case config (#4662)

## [78.0.0] - 2025-10-20
### Changed
- Adding the start commands for MIP-DNA again

## [77.1.1] - 2025-10-20
### Added
- Tests for the existing functionality of the module `FastqFetcher` (#4655)

## [77.1.0] - 2025-10-13
### Added
- Utility class `TypedMock` that can be used when mocking to refer to the mock instance as either a `Mock` or the type being mocked, added to make type checking more convenient. (#4649)

## [77.0.1] - 2025-10-13
### Changed
- Use the new method (#4654)

## [77.0.0] - 2025-10-13
### Fixed
- Revert "Switch start commands for MIP-DNA (#4648)(major)" (#4652)

## [76.0.0] - 2025-10-13
### Changed
- The dev commands have now replaced the old start commands. (#4648)
### Fixed
- Patched older tests since some of them is still in use for mip-rna (#4648)

## [75.4.1] - 2025-10-09
### Added
- Reminder to all delivery messages with Caesar delivery (#4640)

## [75.4.0] - 2025-10-07
### Changed
- Changed analysis cleaning logic to be base on completion timestamp (#4645)
- Removed default value for `before` param in `get_analyses_to_clean` (#4645)

## [75.3.0] - 2025-10-06
### Added
- Option --day-threshold to cg clean illumina-runs (#4639)
### Changed
- Cg clean illumina-runs no longer always uses 21 days as its threshold (#4639)

## [75.2.12] - 2025-10-06
### Added
- Cg workflow mip-dna dev-start
- Cg workflow mip-dna dev-run
- Cg workflow mip-dna dev-config-case
### Fixed
- New lines are added in the managed_variants and gene panel files which were previously malformed for the raredisease dev commands

## [75.2.11] - 2025-10-02
### Changed
- Raredisease: change mosdepth to d4tools output in hk bundle (#4632)

## [75.2.10] - 2025-10-01
### Added
- Reviewer files to Nallo scout load config. (#4607)
### Changed
- How the reviewer files for MIP and raredisease are added; into a common method for MIP, raredisease and Nallo in order to reduce code duplication. (#4607)
### Fixed
- A case level `str_catalog` entry was previously added to the load config for MIP and raredisease, but that is not used in Scout. Changed to a sample level `reviewer_catalog`. (#4607)

## [75.2.9] - 2025-09-30
### Added
- Log how many cases is about to be started by the `start_available` command for the Balsamic, MIP and Nextflow pipelines so that we more easily can verify that the automation does not end prematurely. (#4613)

## [75.2.8] - 2025-09-25
### Added
- Support for checking if any of a sample's files is being archived, and raise an error if that is the case. (#4616)
- Test for this new functionality (#4616)
### Changed
- Modified existing tests to account for new functionality (#4616)
### Fixed
- Removed unused fixtures (#4616)

## [75.2.7] - 2025-09-16
### Added
- Cust201 to LOQUSDB_LONG_READ_CUSTOMERS (#4603)

## [75.2.6] - 2025-09-16
### Changed
- Files currently being retrieved are excluded from new retrieval jobs. (#4609)

## [75.2.5] - 2025-09-15
### Added
- Nallo TRGT variant catalog for housekeeper (#4604)

## [75.2.4] - 2025-09-10
### Fixed
- Case_id non-nullable in CaseSample (#4553)
- Sample_id non-nullable in CaseSample (#4553)

## [75.2.3] - 2025-09-10
### Fixed
- Model dump is sent as kwargs in get_workflow_version (#4592)
- Reworked the output handling of the version output (#4592)

## [75.2.2] - 2025-09-05
### Fixed
- Removes reference to unused property flow_cells (#4590)

## [75.2.1] - 2025-09-04
### Fixed
- The SubprocessSubmitter runs analyses with check False (#4585)

## [75.2.0] - 2025-09-03
### Changed
- Taxprofiler analyses are started with the AnalysisStarter (#4576)

## [75.1.0] - 2025-09-02
### Added
- Integration test that runs the cg command `workflow mip-dna start-available` with one case ready to start. Checks that: (#4543)
- All necessary cli commands and http requests are made (#4543)
- All files are created in the correct place (#4543)
- Additional pytest plugin added: `pytest-httpserver` runs a barebones http server that captures calls made by the code under test. (#4543)
- Added default pytest option `-m not integration` so that integration tests are only run when the `-m integration` flag is added. (#4543)
- Run the integration tests in the GitHub action `tests-coverage` (#4543)

## [75.0.10] - 2025-09-01
### Added
- Nallo QC Peddy kinship (#4426)
- Nallo QC Somalier sex check (#4426)

## [75.0.9] - 2025-09-01
### Added
- Vulture to the pre-commit hooks (#4430)
- Vulture_whitelist.txt for ignoring false positives (#4430)
### Changed
- Removed almost all methods flagged by vulture (#4430)

## [75.0.8] - 2025-08-28
### Fixed
- Removed APIRequest coupling outside of the TrailblazerAPI. (#4502)

## [75.0.7] - 2025-08-27
### Added
- Check that the samples included in the Illumina sample sheet belong to the given Fluffy case and filter out the ones that don't (#4555)

## [75.0.6] - 2025-08-20
### Added
- `get_start_command` method in MicrosaltCaseConfig (#4549)
- Test for the new method (#4549)
### Changed
- Remove `WORKFLOW_LAUNCH_COMMAND_MAP`. (#4549)

## [75.0.5] - 2025-07-31
### Added
- Class TaxprofilerParamsFileCreator (#4509)
- Base model TaxprofilerParameters inheriting from WorkflowParameters (empty as no extra parameters are needed) (#4509)
- Taxprofiler to configurator factory and to analysis starter factory (#4509)
- Dev cli commands: (#4509)
- Dev_config_case (#4509)
- Dev_run (#4509)
- Dev_start (#4509)
- Dev_start_available (#4509)
- Tests for new cli commands (#4509)
### Changed
- Move the constructor from the child classes to the parent ParamsFileCreator. This constructor receives only the servers params file path. Override only in raredisease as it needs store and LIMS (#4509)
### Fixed
- Enhance tests and fixtures of analysis start workflow (#4509)

## [75.0.4] - 2025-07-30
### Added
- Added the -l flag to the Sbatch header to run it as a login-session and thereby loading the bashrc

## [75.0.3] - 2025-07-28
### Changed
- Remove the method removing the microSALT Slurm IDs file (#4529)

## [75.0.2] - 2025-07-23
### Added
- Function that checks if sample is microSALT or Mutant to skip it if it has no reads and do not block the analysis (#4520)
- Tests for new functionality (#4520)

## [75.0.1] - 2025-07-21
### Added
- Mandatory field `repository` for Nallo, Taxprofiler and Tomte (#4515)
- Optional field `pre-run-script` initialised as empty str for Nallo, Taxprofiler and Tomte (#4515)
### Changed
- Updated fixtures (#4515)

## [75.0.0] - 2025-07-17
### Changed
- Removes `revision` as a CLI option for RNAFUSION and raredisease (#4503)
- Removes `stub_run` from the analysis starting flow (#4503)
### Fixed
- Remove tests for deprecated commands and unused RNAFUSION fixtures (#4503)

## [74.1.3] - 2025-07-17
### Added
- Taxprofiler sample sheet creator (#4510)
### Changed
- Validation for existence of fastqfiles relies exclusively on the input fetcher, not in the sample sheet (#4510)
- The return type of `_get_paired_read_paths` changed to a tuple iterator (#4510)

## [74.1.2] - 2025-07-14
### Changed
- Remove io handler usages (#4501)
- Remove writable file from fixtures (#4501)
### Fixed
- Remove usages of io handler (#4501)

## [74.1.1] - 2025-07-14
### Added
- Dev_config_case (#4500)
- Dev_run (#4500)
- Dev_start (#4500)
- Dev_start_available (#4500)
- Tests for these and rnafusion commands (#4500)
### Changed
- Remove special exception of `AnalysisRunningError` in AnalysisStarter `start_available` (#4500)
- Parametrised AnalysisStarter tests on workflow (second parameterisation) (#4500)

## [74.1.0] - 2025-07-10
### Added
- Dev-run CLI command (#4483)
- Dev-start CLI command (#4483)
- Dev-start-available CLI command (#4483)
- Dev-config-case CLI command (#4483)
- RNAFusionSampleSheetCreator (#4483)
- RNAFusionParamsFileCreator (#4483)
### Changed
- Refactored the SampleSheetCreator parent class to have more functionality (#4483)

## [74.0.0] - 2025-07-10
### Added
- Tests for microsalt`start` and `start-available` CLI commands (#4499)
### Changed
- Use only `@click.pass_obj` instead of `@click.pass_context` in new CLI commands (#4499)
- Remove old CLI commands (#4499)
- Removed tests and fixtures for previous CLI commands (#4499)

## [73.2.0] - 2025-07-09
### Changed
- The `post_process_all_runs` now only post-pocesses SMRT cells if the entire run is completed (#4479)

## [73.1.1] - 2025-07-08
### Added
- `tiddit_coverage_wig`, `upd_regions_bed` and `upd_sites_bed` under `sample` in the Scout load config so the corresponding files are uploaded to Scout. (#4425)

## [73.1.0] - 2025-07-08
### Added
- Nallo loqusdb to cg upload (#4471)

## [73.0.5] - 2025-07-08
### Fixed
- Single sample cases gets a slurm job id file name with the whole sample id. (#4496)

## [73.0.4] - 2025-07-02
### Fixed
- WES Raredisease cases are not expected to have a vcf-str file in the Scout upload (#4485)

## [73.0.3] - 2025-07-02
### Changed
- Update raredisease params creation (#4482)

## [73.0.2] - 2025-06-30
### Fixed
- Removed case_id CLI argument from cg workflow microsalt dev-start-available (#4481)

## [73.0.1] - 2025-06-30
### Added
- Error handling (#4206)
### Changed
- The way samples to clean are fetched, now we verify if they belong to a case that is not cleanable. (#4206)

## [73.0.0] - 2025-06-26
### Added
- Main method to get versions in the `HousekeeperAPI` gets version entry id as parameter, not bundle name and date (#4455)
- Remove optional parameter `analysis_completed_at` from `generate_delivery_report` CLI command (#4455)
### Changed
- Make the `AnalysisAPI.create_housekeeper_bundle` method return a tuple of Housekeeper bundle and version (instead of returning None) (#4455)
- Make several delivery report API methods receive for parameter an Analysis object instead of the `analysis.completed_at date` (#4455)
### Fixed
- Cleans unused functions and tests (#4455)

## [72.0.4] - 2025-06-26
### Fixed
- Workflow version is allowed to be up to 64 characters (#4470)
- Data_analysis is not nullable (#4470)

## [72.0.3] - 2025-06-26
### Added
- Nallo upload to loqusDB using cg (#4344)

## [72.0.2] - 2025-06-26
### Added
- A flag "-ifnewer" to the retrieval command. (#3857)
### Changed
- This flag will _"The ifnewer option replaces an existing file with the latest backup version only if the backup version is newer than the existing file."_ More on this here: https://www.ibm.com/docs/en/spectrum-protect/8.1.11?topic=reference-ifnewer (#3857)
### Fixed
- This will fix this issue: https://github.com/Clinical-Genomics/cg/issues/3843 (#3857)

## [72.0.1] - 2025-06-26
### Added
- Added the ability to filte on application.is_archived in the application_version table (#4469)

## [72.0.0] - 2025-06-26
### Added
- MicroSALT CLI commands `dev-run`, `dev-start` and `dev-start-available` (#4227)
- AnalysisStarter (#4227)
- AnalysisStarterFactory (#4227)
- ConfiguratorFactory (#4227)
- Configurator (Parent) (#4227)
- MicrosaltConfigurator (Child) (#4227)
- NextflowConfigurator (Child) (#4227)
- MicrosaltConfigFileCreator (#4227)
- RarediseaseConfigFileCreator (#4227)
- RarediseaseParamsFileCreator (#4227)
- ManagedVariantsFileCreator (#4227)
- GenePanelsFileCreator (#4227)
- PipelineExtension (Parent) (#4227)
- RarediseaseExtension (Child) (#4227)
- InputFetcher (Parent) (#4227)
- FastqFetcher (Child) (#4227)
- Submitter (Parent) (#4227)
- SubprocessSubmitter (Child) (#4227)
- SeqeraPlatformSubmitter (Child) (#4227)
- SeqeraPlatformClient (#4227)
- Tracker (Parent) (#4227)
- MicrosaltTracker (Child) (#4227)
- NextflowTracker (Child) (#4227)
- Tests (#4227)

## [71.4.0] - 2025-06-25
### Changed
- Remove contamination check (#4463)

## [71.3.1] - 2025-06-25
### Added
- Ability to filter on is_archived in the ApplicationView (#4466)

## [71.3.0] - 2025-06-24
### Added
- Indexed column housekeeper_version_id to the Analysis table (#4459)

## [71.2.0] - 2025-06-23
### Changed
- Sequencing QC removed from start-available (#4443)
- Sequencing QC added as a query filter in start-available (#4443)
- Removed special `is_case_ready_for_analysis` from MIP-DNA and Balsamic (#4443)
- Removed the extra `_is_case_to_be_analyzed` check in read.py (#4443)

## [71.1.6] - 2025-06-23
### Changed
- Raredisease Delivery report: mapping fraction to percentage (#4458)

## [71.1.5] - 2025-06-23
### Fixed
- Search for names or internal ids in the CaseSample form. Speeds up the form (#4457)

## [71.1.4] - 2025-06-18
### Added
- <TICKET>_create_inbox job creates the directory using mkdir -p which will not fail should the directory already exist (#4446)
- <CASE_ID>_rsync job depends on the above job using the sbatch parameter --dependency=afterok:<JOB_ID> and so will not run before it's completed. (#4446)

## [71.1.3] - 2025-06-17
### Fixed
- Fix nextflow store available (#4451)

## [71.1.2] - 2025-06-17
### Added
- Sentinel variable that changes from True to False when an exception is caught for the store-available commands (#4450)

## [71.1.1] - 2025-06-17
### Fixed
- Analysis, orders and cases all have speedier forms. (#4449)

## [71.1.0] - 2025-06-16
### Changed
- Updated 1508 order form fixtures to version 35 (#4444)
- Parametrise orderform tests (#4444)

## [71.0.8] - 2025-06-16
### Added
- Customer columns link to the Customer table (#4442)
- Illumina Flow cell links to the Illumina Sample Sequencing Metrics table (#4442)
- Pacbio SMRT Cell links to the Pacbio Sample Sequencing Metrics table (#4442)
- Sample links to Application (#4442)
- Pool links to application (#4442)
- Application links to ApplicationVersion (#4442)

## [71.0.7] - 2025-06-13
### Fixed
- Patch case latest analysed ensuring dates are not None (#4445)

## [71.0.6] - 2025-06-11
### Changed
- `cases.analysis[0]` ocurrences with the correct store methods to fetch the latest completed analysis (#4439)
- `cases.analysis` is now sorted by `created_at` which is never None. (#4439)

## [71.0.5] - 2025-06-10
### Added
- Microsalt-version to protected tags for MICROSALT workflow and organized alphabetically (#4436)

## [71.0.4] - 2025-06-09
### Added
- New CRUD function `get_latest_started_analysis_for_case` with tests (#4435)
### Changed
- AnalysisAPI method `update_analysis_as_completed_statusdb` so that it uses the new function (#4435)

## [71.0.3] - 2025-06-09
### Changed
- Make the Delete, Create and Update handlers inherit from the ReadHandler instead of BaseHandler (#4428)
- Remove ReadHandler from Store constructor (#4428)
- Rename all Hanlder classes adding the Mixin suffix (#4428)
- Move session methods from Store class to BaseHandler (#4428)
- Remove the instantiation of the Handlers in the __init__ of the Store (#4428)
- Removes the `__init__` from all handlers, all of them will use the constructor of the parent class (`BaseHandler`) (#4428)

## [71.0.2] - 2025-06-05
### Fixed
- The version would be fetched through `completed_at` instead of `started_at` of the Analysis object (#4431)
- The `completed_at` date of teh Analysis object will be the timestamp of the bundle generated by HermesAPI (#4431)

## [71.0.1] - 2025-06-04
### Fixed
- Nallo is now a valid option for `cg clean tower-past-run-dirs (#4424)

## [71.0.0] - 2025-06-03
### Added
- Add new value for case action: top-up, set this value on a case to mark it for top up (#4399)
- Analysis row in StatusDB created at the start of analysis instead of on completion (#4399)
- Link analysis in StatusDB with analysis in Trailblazer by adding the column `trailblazer_id` to the table in StatusDB (#4399)

## [70.0.8] - 2025-05-26
### Fixed
- Order of indices is now correct (#4416)

## [70.0.7] - 2025-05-23
### Fixed
- Loading RNA outlier variants to Scout only happens if files exist (#4414)

## [70.0.6] - 2025-05-22
### Changed
- Update gene_panel.py (#4412)

## [70.0.5] - 2025-05-22
### Added
- Allow revision flag upon resuming tower runs (#4409)

## [70.0.4] - 2025-05-21
### Changed
- Change suffix from sorted_md to sort_md (#4405)

## [70.0.3] - 2025-05-20
### Fixed
- Wrap a GoogleAuthError in our endpoint (#4404)

## [70.0.2] - 2025-05-14
### Changed
- Refactor StoreMetagenomeOrderService to create cases for each sample and add case testing (#4398)

## [70.0.1] - 2025-05-13
### Added
- Create a csv file with the corresponding customer and internal sample ids upon raredisease config-case (#4390)

## [70.0.0] - 2025-05-13
### Fixed
- Remove function `hk_bundle_files` from cg/cli/clean.py (#4395)
- Remove all functions that were only used there (#4395)
- Remove all tests of removed functions (#4395)

## [69.10.10] - 2025-05-13
### Fixed
- Fix bind in most recent alembic migration (#4396)

## [69.10.9] - 2025-05-13
### Changed
- Taxprofiler Sequencing QC is that all samples should have reads. (#4397)

## [69.10.8] - 2025-05-12
### Added
- `status: prioritized` to the scout load config if the priority of the case is `priority` or `express` (#4392)

## [69.10.7] - 2025-05-12
### Added
- BeforeValidator in ExcelSample model to make sure that the empty value for `require_qc_ok` `tumour` are converted to Non before validation (#4394)

## [69.10.6] - 2025-05-12
### Changed
- Current version of microbial_sequencing ordeform updated from 1 to 2 (#4360)

## [69.10.5] - 2025-05-08
### Added
- `--limit` flag for number of cases to start with the `start-available` command for mip and balsamic. (#4381)
### Changed
- Changed `mip_dna_context` to actually contain cases ready to be analysed that could be picked up by the `start-available` command. (#4381)

## [69.10.4] - 2025-05-08
### Added
- Endpoint /orders/index_sequences for fetching index sequences (#4371)
### Changed
- RML and Fluffy orders need to use v20 of the order form (#4371)

## [69.10.3] - 2025-05-08
### Changed
- Nallo delivery report link to scout38 (#4387)

## [69.10.2] - 2025-05-07
### Added
- Step and UDF names of the Revio prep to the LIMS constants (#4382)
- Step and UDF names of the Revio sequencing to the LIMS constants (#4382)

## [69.10.1] - 2025-05-07
### Fixed
- Validate_existing_samples_compatible_with_order_type used in the Nallo validation (#4384)

## [69.10.0] - 2025-05-07
### Added
- New case validation rule `validate_samples_in_case_have_same_prep_category` for Raredisease and MIP-DNA (#4363)
- Utils function to get prep categories for samples of a case (#4363)
- Error model for multiple samples in a case having same prep category (#4363)
- Models for the validation of raredisease orders inheriting from MIP: (#4363)
- Order (fixing type hints for cases) (#4363)
- Case (fixing type hints for sample and for methods (#4363)
- Sample (#4363)
- Allowed Raredisease delivery types (#4363)
- Validation rules (#4363)
- Entry for Raredisease to Storing registry (#4363)

## [69.9.0] - 2025-05-06
### Added
- Nallo order form fixture (#4374)
- Support for parsing Nallo order forms (#4374)
### Changed
- Bumped Pacbio raw data version to v2 (#4374)

## [69.8.6] - 2025-05-06
### Changed
- Nallo Scout do not upload assembly file (#4380)

## [69.8.5] - 2025-05-05
### Changed
- Make alembic revision 8e0b9e03054d idempotent (#4378)

## [69.8.4] - 2025-05-05
### Changed
- Additional metrics in Nallo delivery report (#4377)

## [69.8.3] - 2025-05-05
### Added
- Migration to create copies of all MIP_DNA entries in the order_type_application table with RAREDISEASE as order_type instead (#4375)

## [69.8.2] - 2025-05-05
### Added
- New LIMS step information for the Watchmaker prep (#4372)

## [69.8.1] - 2025-04-28
### Added
- Validation of the capture kit for fastq orders (#4366)

## [69.8.0] - 2025-04-28
### Added
- Reset_optional_capture_kits rule (#4331)

## [69.7.2] - 2025-04-28
### Changed
- Now uses Clinical-Genomics/bump2version-ci@2.0.3 instead of Clinical-Genomics/bump2version-ci@v3 (#4369)

## [69.7.1] - 2025-04-28
### Added
- Rule for validating that existing samples are compatible with the order type (#4354)
- Support for filtering samples in collaboration on order type (#4354)

## [69.7.0] - 2025-04-28
### Changed
- Tag orders containing samples with external data samples with "external-data" (#4340)

## [69.6.4] - 2025-04-28
### Added
- Error throwing when a parameter is defined both in the servers yaml and built from cg (#4330)
### Changed
- Change logic for skip_germlinevariant calling in config-case (#4330)
- The default capture kit will be defined from servers configs, not cg (#4330)

## [69.6.3] - 2025-04-28
### Added
- Fix tag set for d4 file (#4368)

## [69.6.2] - 2025-04-28
### Added
- Raredisease to the `OrderType` Strenum (#4365)
- Alembic migration to allow new ordertype in the `order_type_application` table (#4365)

## [69.6.1] - 2025-04-24
### Added
- Tumour field on MIP-RNA samples (#4356)

## [69.6.0] - 2025-04-24
### Added
- Models and validation rules to make Nallo orderable in cg (#4342)
- Connect Nallo with CaseStoring service (#4342)

## [69.5.3] - 2025-04-23
### Changed
- Remove raredisease adapter QC check (#4325)

## [69.5.2] - 2025-04-22
### Fixed
- Model_config instead of class Config (#4324)

## [69.5.1] - 2025-04-22
### Fixed
- The url of Scout38 was missing the `.sys.` (#4346)
- For Nallo cases with delivery type `scout` the old Scout url would have been shown. Now it always checks for the workflow to choose the url. (#4346)

## [69.5.0] - 2025-04-22
### Added
- Nallo as an ordertype (#4347)
- Alembic migration to update the ordertype_application table with Nallo as ordertype (#4347)

## [69.4.6] - 2025-04-22
### Added
- Remove dupliate entry for nallo housekeeper filepath (#4353)

## [69.4.5] - 2025-04-22
### Added
- Add peddy to nallo scout upload (#4335)
- Add hificnv_coverage to nallo scout upload (#4335)
- Add maf coverage to nallo scout upload (#4335)
- Add alignement to nallo scout upload (#4335)
- Add assembly alignment to nallo scout upload (#4335)
### Fixed
- Removed double definition of NALLO_CASE_TAGS and NALLO_SAMPLE_TAGS (#4335)

## [69.4.4] - 2025-04-22
### Fixed
- Workflow instead of workflow (#4352)

## [69.4.3] - 2025-04-16
### Added
- Add delivery message support for nallo (#4332)

## [69.4.2] - 2025-04-16
### Added
- Data delivery types containing `raw-data` to the allowed types for delivery report creation (#4345)

## [69.4.1] - 2025-04-16
### Added
- Peddy files to housekeeper (#4338)
- Sv vcf outputs per caller (#4338)
### Changed
- Name of repeats vcf and bam (#4338)

## [69.4.0] - 2025-04-16
### Added
- Delivery types `RAW_DATA_ANALYSIS `, `RAW_DATA_ANALYSIS_SCOUT `and `RAW_DATA_SCOUT ` in `DataDelivery ` strenum (#4329)
- `{bam}` to the `RAW_DATA_ANALYSIS_SAMPLE_TAGS` (#4329)
- Support for the new delivery types in the`DeliveryServiceFactory` (#4329)
### Changed
- Removed `BamDeliveryTagsFetcher` and make BAM delivery use SampleAndCaseDeliveryTagsFetcher (#4329)

## [69.3.4] - 2025-04-16
### Changed
- Two instances of the Scout api will now be instantiated in the CGConfig. (#4333)
- The workflow is used to distinguish which scout instance should be used. (#4333)

## [69.3.3] - 2025-04-14
### Fixed
- Well position format is only validated if the well position is provided. (#4323)

## [69.3.2] - 2025-04-11
### Fixed
- Nallo upload missing argument (#4334)

## [69.3.1] - 2025-04-10
### Added
- Add analysis as parameter for method include_pedigree_picture (#4336)

## [69.3.0] - 2025-04-09
### Added
- Nallo scout upload (#4205)

## [69.2.2] - 2025-04-08
### Added
- Default option to disable normal filtration for tumor normal matched TGA analyses in balsamic (#4157)

## [69.2.1] - 2025-04-07
### Added
- Deliver message logic for taxprofiler (#4328)

## [69.2.0] - 2025-04-03
### Added
- Nallo QC sex check (#4288)
### Changed
- Nallo QC median coverage threshold to 20. (#4288)

## [69.1.26] - 2025-04-02
### Added
- Tags `{"storage", "assembly"}` to `MICROSALT_ANALYSIS_SAMPLE_TAGS`. (#4299)

## [69.1.25] - 2025-04-02
### Added
- Logic for differing SLA for order tickets (#4274)

## [69.1.24] - 2025-03-31
### Added
- Add validation for capture kit (#4319)

## [69.1.23] - 2025-03-27
### Changed
- Date check is now done on the correct directory (#4312)

## [69.1.22] - 2025-03-26
### Changed
- Priority order so that clinical_trials does not have the highest priority. (#4300)

## [69.1.21] - 2025-03-25
### Fixed
- The deletion now occurs on the actual directory provided (#4308)

## [69.1.20] - 2025-03-24
### Added
- Kidney and CAKUT gene panels to the clinical master list (#4303)

## [69.1.19] - 2025-03-20
### Added
- Nallo delivery report (#4298)
### Changed
- Sample metric models for nextflow pipelines are explicitly invoked (#4298)

## [69.1.18] - 2025-03-19
### Added
- Cg workflow nallo store-available (#4287)

## [69.1.17] - 2025-03-18
### Fixed
- Fix( parsing no delivery option) (#4294)

## [69.1.16] - 2025-03-17
### Changed
- Remove multiqc files from fixture and update software version paths (#4291)

## [69.1.15] - 2025-03-17
### Fixed
- Revert "Add Nallo delivery report (#4198)" (#4292)

## [69.1.14] - 2025-03-14
### Fixed
- Fix #4149 (#4285)

## [69.1.13] - 2025-03-14
### Added
- Nallo delivery report (#4198)
### Changed
- Explicitly specify pydantic models for each QCMetrics BaseModel. (#4198)

## [69.1.12] - 2025-03-13
### Fixed
- JSONOrderformParser supports all order types instead of workflows. (#4286)

## [69.1.11] - 2025-03-12
### Added
- Add post processing filter for unfinished run transfers (#4279)

## [69.1.10] - 2025-03-12
### Changed
- Cli-search (#4280)

## [69.1.9] - 2025-03-12
### Changed
- Move annotated repeats from sample to case (#4278)

## [69.1.8] - 2025-03-10
### Added
- Cg workflow nallo start-available (#4169)

## [69.1.7] - 2025-03-08
### Changed
- Improvements to sbatch header template: (#4269)
- Enhancements to Slurm API: (#4269)
- Updates to sbatch model: (#4269)

## [69.1.6] - 2025-03-06
### Added
- Nallo to statusDB limitations table (#4264)

## [69.1.5] - 2025-03-05
### Changed
- Is_compression_pending is a property of CompressionData (#4257)
- Is_fastq_compression_possible is a property of CompressionData (#4257)
- Is_spring_decompression_possible is a property of CompressionData (#4257)
- Is_fastq_compression_done is a property of CompressionData (#4257)
- Is_spring_decompression_done is a property of CompressionData (#4257)

## [69.1.4] - 2025-03-04
### Changed
- Smrt_cell_ids parsed as a list in the pacbio sample sequencing metrics endpoint (#4262)

## [69.1.3] - 2025-03-03
### Changed
- Update nallo file paths (#4258)

## [69.1.2] - 2025-03-03
### Changed
- Made the qos of a case a model property instead of a function of the analysis API (#4252)
### Fixed
- Moved the test to the correct module (#4252)

## [69.1.1] - 2025-02-27
### Changed
- Raredisease use picardtools duplication rate output in metrics-deliver (#4245)

## [69.1.0] - 2025-02-26
### Changed
- The container_name field now needs to adhere to the pattern ^[A-Za-z0-9_]*$ (#4174)

## [69.0.1] - 2025-02-26
### Fixed
- If the optional files do not exist, they are not uploaded (#4233)

## [69.0.0] - 2025-02-25
### Changed
- Version of the orderforms (#4246)
### Fixed
- Orderform fixtures (#4246)

## [68.1.2] - 2025-02-25
### Changed
- Update file name (#3950)

## [68.1.1] - 2025-02-25
### Changed
- If an RNA sample has no subject id set, the upload raises a more descriptive error. (#4244)

## [68.1.0] - 2025-02-25
### Added
- `get_genome_build` method in the `TomteAnalysisAPI` that overrides the parent method and returns HG38 (#4224)
### Changed
- Update `upload_rna_genome_build_to_scout` without calling the get_genome_build from the deleted module but using directly HG38 (#4224)
### Fixed
- The function `get_genome_build` in the parent class `NFAnalysisAPI` contained only the logic for Tomte, as this method is overridden in all the NF-Pipelines. Its logic was removed and now it raises a `NotImplementedError`. (#4224)
- Remove `cg/meta/workflow/utils/genome_build_helpers.py` as contained functions used to fetch the reference genome for tomte cases from the database (#4224)
- Removed `reference_genome` in the `TomteSample` in the ordering models (#4224)
- Remove reference_genome from Tomte Fixtures (#4224)

## [68.0.17] - 2025-02-20
### Fixed
- Missing file names in raredisease delivery report. (#4200)

## [68.0.16] - 2025-02-18
### Changed
- The JSON order form parser is not restricted to a subset of workflows. (#4221)

## [68.0.15] - 2025-02-18
### Changed
- Deprecate os ticket (#4220)

## [68.0.14] - 2025-02-18
### Changed
- Centralise app config (#4219)

## [68.0.13] - 2025-02-17
### Fixed
- Validation directory renamed from workflows to order_types (#4201)

## [68.0.12] - 2025-02-17
### Changed
- Clicking Delivery contact, Lab contact or Primary contact links you to the User table in the admin view. (#4208)

## [68.0.11] - 2025-02-17
### Changed
- The link generated by clicking a sample or case entry in statusDB web to provide an exact match. (#4202)

## [68.0.10] - 2025-02-14
### Changed
- Removed raredisease adapter content check from picardtools and WES depth threshold. (#4207)

## [68.0.9] - 2025-02-13
### Added
- Add upload_genotypes to raredisease upload command (#4203)

## [68.0.8] - 2025-02-12
### Added
- Store and store housekeeper command for nallo, resources might change slightly in a subsequent PR (#4171)

## [68.0.7] - 2025-02-12
### Changed
- We always generate the index sequence from the index number and index. (#4187)

## [68.0.6] - 2025-02-12
### Fixed
- Acronyms are in all caps (#4193)
- MIPDNADeliveryType introduced (#4193)

## [68.0.5] - 2025-02-12
### Added
- Validation preventing placing orders of balsamic or balsamicUMI cases containing only 1 WGS sample which is normal. (#4194)

## [68.0.4] - 2025-02-12
### Fixed
- Deleting a case cascades even in the SQL database (#4188)

## [68.0.3] - 2025-02-11
### Added
- Instructions to install the optional development dependencies. (#4196)

## [68.0.2] - 2025-02-11
### Fixed
- The OrderTypeApplication table no longer references BALSAMIC_QC. (#4195)

## [68.0.1] - 2025-02-11
### Fixed
- Max restriction of 64 characters on the order name (#4197)

## [68.0.0] - 2025-02-10
### Changed
- Remove balsamic qc (#4192)

## [67.3.1] - 2025-02-10
### Added
- Validation rule ensuring that each new case contains at least one affected sample in MIP-DNA (#4191)
- Validation rule ensuring that existing cases without at least one affected sample is not allowed in MIP-DNA (#4191)
- Type hint for statuses of new MIP-DNA samples only allows for affected or unaffected (#4191)

## [67.3.0] - 2025-02-10
### Added
- Endpoint for fetching Pacbio sequencing runs based on run name (#4185)

## [67.2.2] - 2025-02-06
### Fixed
- Check if the case is old before checking if it contains existing samples (#4186)

## [67.2.1] - 2025-02-06
### Changed
- Demultiplexing job now requests 48 cores (#4184)

## [67.2.0] - 2025-02-06
### Added
- Endpoint for fetching Pacbio sample sequencing metrics (#4180)

## [67.1.10] - 2025-02-06
### Added
- Raredisease QC check adapter content (#4183)
- Raredisease QC check sample contamination (#4183)

## [67.1.9] - 2025-02-05
### Changed
- Method `store_order_data_in_status_db` from `StoreFastqOrderService` (#4182)
- The unit test of the method above (#4182)

## [67.1.8] - 2025-02-04
### Fixed
- Fix page index starting from 0 (#4178)

## [67.1.7] - 2025-02-04
### Fixed
- Fix excel orderforms (#4177)

## [67.1.6] - 2025-02-04
### Added
- Case service for the endpoint (#3962)
### Changed
- Functions in the crud that return cases/samples so that they return also the total number of cases/samples (#3962)
- Moved application and sample services to we_services directory (#3962)
- Improve the file structure of web services (#3962)

## [67.1.5] - 2025-02-04
### Added
- Ticket with only existing samples get the status open (#4150)

## [67.1.4] - 2025-02-04
### Added
- If a ticket contains already existing data, a tag "existing-data" is added (#4148)

## [67.1.3] - 2025-02-03
### Added
- GC dropout QC check to raredisease (#3838)
- AT dropout QC check to raredisease (#3838)

## [67.1.2] - 2025-02-03
### Fixed
- Case priority is set on samples for case orders (#4176)

## [67.1.1] - 2025-02-03
### Added
- Add technical debt issue template (#4041)

## [67.1.0] - 2025-02-03
### Added
- Add parameters to the nextflow config (#3853)

## [67.0.19] - 2025-02-03
### Fixed
- Set the LIMS internal id for metagenome orders (#4175)

## [67.0.18] - 2025-02-03
### Changed
- The union typing of the `NextflowAnalysis` attribute `smaple_metrics` and explicitly specify to choose union models according to `left-to-right` (#4165)

## [67.0.17] - 2025-01-30
### Fixed
- Determining the type of order/case/sample/case_sample error is not by length of loc (#4170)

## [67.0.16] - 2025-01-30
### Fixed
- Tomte delivery messages use the same logic as MIP-RNA (#4172)

## [67.0.15] - 2025-01-30
### Changed
- The RNA uploads to Scout use the query logic found in the ReadHandler (#4145)
- More robust error raising in the ReadHandler for when there are multiple matching DNA samples or when no subject id is passed. (#4145)

## [67.0.14] - 2025-01-30
### Added
- Cg workflow nallo panel (#4155)
### Changed
- Cg workflow nallo config-case triggers panel generation (#4155)

## [67.0.13] - 2025-01-30
### Added
- List of nallo file paths for hermes (#4156)
- Generate deliverables.yaml file for nallo (#4156)

## [67.0.12] - 2025-01-29
### Added
- Cg workflow nallo metrics-deliver (#4142)
- Nallo to config-case pytests (#4142)

## [67.0.11] - 2025-01-29
### Fixed
- Region code only set by validator if region is set (#4168)
- Original lab address only set by validator if original lab is set. (#4168)

## [67.0.10] - 2025-01-29
### Added
- Add scout delivery types to tomte (#4167)

## [67.0.9] - 2025-01-28
### Fixed
- Admins are allowed to place orders for all customers (#4163)

## [67.0.8] - 2025-01-28
### Fixed
- Validate_father_in_same_case works with existing samples (#4160)
- Validate_mother_in_same_case works with existing samples (#4160)
- Validate_fathers_are_male works with existing samples (#4160)
- Validate_mothers_are_female works with existing samples (#4160)

## [67.0.7] - 2025-01-28
### Added
- Option to use BWA-MEM in fluffy analysis commands (#4158)

## [67.0.6] - 2025-01-27
### Added
- Add d4_file to raredisease scout load config (#4154)

## [67.0.5] - 2025-01-27
### Fixed
- Fix tests from improve order flow (#4152)

## [67.0.4] - 2025-01-27
### Fixed
- New lines for every sample (#4147)
- Use sample priority name to avoid ints (#4147)

## [67.0.3] - 2025-01-23
### Fixed
- Typo in paths for raredisease (#4151)

## [67.0.2] - 2025-01-23
### Fixed
- Skip_reception_control gets converted to False if null (#4146)

## [67.0.1] - 2025-01-23
### Changed
- Typo in stranger step (#4141)
- Path to chromograph files sites and regions (#4141)

## [67.0.0] - 2025-01-23
### Added
- New validation flow for all order types (#3815)
- New OrderValidationService (#3815)
- New BaseModel's for all order types performing basic validation such as type checking (#3815)
- Rules written for each validation for more complicated rules, including database checks and fields dependent on each other. (#3815)
- New endpoint for validating orders (#3815)
- New Request handling in submit_order (#3815)

## [66.1.0] - 2025-01-22
### Changed
- Allows the container path to be configured in the config of the CLI (#4136)

## [66.0.2] - 2025-01-20
### Fixed
- WTForms locked to version 3.0.0 for now (#4122)

## [66.0.1] - 2025-01-20
### Added
- Workflow nallo start (#4112)

## [66.0.0] - 2025-01-20
### Changed
- Standardize to python project instead of Poetry (#4068)
- Remove cache to allow updates to be installed (#4068)
- Update several packages (#4068)

## [65.0.16] - 2025-01-17
### Added
- Cg workflow run nallo (#4106)

## [65.0.15] - 2025-01-16
### Added
- Cg workflow nallo config-case (#4098)

## [65.0.14] - 2025-01-16
### Added
- Email report sending to MutantUploadAPI upload command (#4100)

## [65.0.13] - 2025-01-15
### Changed
- Remove application version from the delivery report template. (#4076)

## [65.0.12] - 2025-01-14
### Fixed
- Fix(Vulnerability) Update virtualenv (#4079)

## [65.0.11] - 2025-01-14
### Added
- Nallo to cg workflow cli (#4077)

## [65.0.10] - 2025-01-13
### Fixed
- Fix(assignment maf cases to special order) (#4053)

## [65.0.9] - 2025-01-13
### Fixed
- Fix(tb auth) (#4072)

## [65.0.8] - 2025-01-10
### Fixed
- Revert "feat(change token genertion towards tb api) (#4060) (patch)" (#4069)

## [65.0.7] - 2025-01-09
### Changed
- Feat(change token genertion towards tb api) (#4060)

## [65.0.6] - 2025-01-08
### Changed
- Configure multiqc so that it can handle more than 500 rows (#4058)

## [65.0.5] - 2025-01-07
### Changed
- Removed the `getattr` redirect on `HousekeeperAPI` (#4051)

## [65.0.4] - 2025-01-07
### Fixed
- Copies README file into container (#4055)
- Split install of requirements our of install of actual cg-repo (#4055)

## [65.0.3] - 2025-01-07
### Fixed
- Renamed NFAnalysisAPI.config to NFAnalysisAPI.workflow_config_path (#4049)

## [65.0.2] - 2025-01-02
### Fixed
- Use correct customer when uploading RNA-omics results to scout (#4046)

## [65.0.1] - 2024-12-20
### Fixed
- Fix a bug (#4040)

## [65.0.0] - 2024-12-18
### Changed
- Feature(streamline mutant delivery and upload) (#3916)

## [64.5.31] - 2024-12-17
### Changed
- Order form 1508 bumped to version 33 (#4018)

## [64.5.30] - 2024-12-17
### Changed
- Microbial fastq orders containing samples which the customer has used in a previous order do not pass validation. (#4019)

## [64.5.29] - 2024-12-16
### Changed
- Remove the feature to link orders to an existing ticket (#4013)

## [64.5.28] - 2024-12-11
### Fixed
- Added a `samefile` check to ensure the sample sheet from Housekeeper is not copied if it already matches the existing sample sheet in the sequencing run directory. (#4012)

## [64.5.27] - 2024-12-11
### Changed
- Set ticket create to pending status (#4015)

## [64.5.26] - 2024-12-11
### Changed
- Update Paramiko and cryptography to remove test warnings (#4008)

## [64.5.25] - 2024-12-09
### Changed
- Use Hermes container instead of Conda env. (#3992)
- Add container mount volume to cg config and use it to switch context (#3992)

## [64.5.24] - 2024-12-05
### Fixed
- Controls ran with slurm qos express have the priority in trailblazer corresponding to the priority in statusDB (#3991)

## [64.5.23] - 2024-12-03
### Added
- Error raising for when no matching DNA cases are found. (#3987)
### Changed
- Simplified code structure. (#3987)

## [64.5.22] - 2024-12-03
### Fixed
- The cases field in the response from the order form parser is only populated for relevant order types (#3990)

## [64.5.21] - 2024-12-03
### Added
- Add Nallo to analysis options (#3989)

## [64.5.20] - 2024-12-02
### Changed
- Removed AnalysisType from constants.py (#3982)
- Moved AnalysisType to tb.py (#3982)
- Renamed AnalysisTypes to AnalysisType (#3982)

## [64.5.19] - 2024-11-28
### Fixed
- Sequencing metrics are excluded from the edit sample flask form (#3984)

## [64.5.18] - 2024-11-28
### Added
- Crud functions to retrieve dna cases related to an case. (#3902)
- Logic for generation of delivery messages for mip-rna. (#3902)

## [64.5.17] - 2024-11-28
### Added
- Add( rich click to cg) (#3975)

## [64.5.16] - 2024-11-28
### Changed
- Refactor 2 (#3977)

## [64.5.15] - 2024-11-27
### Fixed
- Pagination is applied even when workflow is not set (#3981)

## [64.5.14] - 2024-11-27
### Changed
- Set parameters in params file, and not config (#3965) | major

## [64.5.13] - 2024-11-27
### Changed
- Remove unused AnalysisType rna (#3973)

## [64.5.12] - 2024-11-26
### Changed
- Rename PrpeCategory to SeqLibPrepCategory (#3961)
- Move the class to sequencing.py under constants (#3961)
- Removed implicit import from constant/__init__.py (#3961)
- DRY: Removed SequencingMethod as it is dictated by SeqLibPrepCategory (#3961)

## [64.5.11] - 2024-11-25
### Changed
- Refactor(decompose sample file formatter) (#3960)

## [64.5.10] - 2024-11-25
### Changed
- Add Gunicorn config (#3894)
- Update werkzeug (#3894)

## [64.5.9] - 2024-11-25
### Added
- Static method `_convert_workflow` in `DeliveryServiceFactory` that patches the workflow of microbial fastq cases as Microsalt (#3958)
- Unit test for new function (#3958)
### Changed
- The parameters of the public function `build_delivery_service` from `DeliveryServiceFactory` to receive case and delivery_type instead of Workflow and delivery_type (#3958)
### Fixed
- All calls to `build_delivery_service` with the new parameters (#3958)
- Tests for `build_delivery_service` (#3958)

## [64.5.8] - 2024-11-20
### Changed
- Refactor get-families-with-samples (#3957)

## [64.5.7] - 2024-11-20
### Changed
- Get_families_with_analyses (#3928)

## [64.5.6] - 2024-11-20
### Changed
- Refactor cases_to_analyse (#3926)

## [64.5.5] - 2024-11-19
### Changed
- Https://github.com/Clinical-Genomics/cg/pull/3427 (#3408)

## [64.5.4] - 2024-11-19
### Fixed
- Samples in tubes get their well position set to None (#3955)

## [64.5.3] - 2024-11-19
### Changed
- Increase memory for multiqc (#3952)

## [64.5.2] - 2024-11-19
### Fixed
- Buffer is removed as a field from the PacbioSample (#3953)
- The test fixture for a pacbio order form has been patched. (#3953)

## [64.5.1] - 2024-11-18
### Added
- Isort config to `pyproject.toml` file (#3944)

## [64.5.0] - 2024-11-13
### Added
- Taxprofiler excel order form test fixture (#3935)
### Changed
- 1508 orderforms need to be version 32 (#3935)

## [64.4.25] - 2024-11-13
### Fixed
- Fix(balsmic workflow fetching order view) (#3933)

## [64.4.24] - 2024-11-12
### Changed
- Unified the config and param file generation for rnafusion with the other nf workflows, using https://github.com/Clinical-Genomics/servers/pull/1467 (#3868)

## [64.4.23] - 2024-11-12
### Fixed
- Fix(order display front end) (#3931)

## [64.4.22] - 2024-11-12
### Changed
- Technical debt( rework order.workflow column) (#3929)

## [64.4.21] - 2024-11-11
### Added
- Fields for rank_model_version (snv and sv), as well as rank rank_score_threshold for raredisease scout upload (#3865)

## [64.4.20] - 2024-11-11
### Changed
- 3714 Validate sample sex in cg add relationship Command (#3863)

## [64.4.19] - 2024-11-11
### Added
- Fixture for orderform 1604-19 (#3906)
### Changed
- The version of the orderform in the constants (#3906)
- Remove old orderform (#3906)

## [64.4.18] - 2024-11-11
### Changed
- Restart branch (#3893)

## [64.4.17] - 2024-11-06
### Added
- Information on what cases the delivery message was generated for. (#3911)

## [64.4.16] - 2024-11-06
### Changed
- Application.order_types is a modifiable list (#3912)

## [64.4.15] - 2024-11-05
### Changed
- Refactor Analysis model for Balsamic (#3885)

## [64.4.14] - 2024-10-30
### Changed
- #2396 get the latest archived flowcell (#3751)

## [64.4.13] - 2024-10-30
### Added
- Add(delete fc command) (#3900)

## [64.4.12] - 2024-10-30
### Fixed
- Typo in mutant QC constant `FRACTION_OF_SAMPLES_WITH_FAILED_QC_THRESHOLD` (#3901)

## [64.4.11] - 2024-10-29
### Added
- Add(pacbio orderform parsing) (#3899)

## [64.4.10] - 2024-10-29
### Changed
- Microbial Sample (#3886)
- Fixtures from Microsalt and SARS-Cov2 (#3886)

## [64.4.9] - 2024-10-28
### Added
- VEO-IBD to clinical master list (#3898)

## [64.4.8] - 2024-10-28
### Changed
- /applications/order_type only returns applications which have versions (#3881)

## [64.4.7] - 2024-10-28
### Fixed
- Internal_id is now set to the LIMS-ID when submitting an order (#3883)

## [64.4.6] - 2024-10-24
### Fixed
- Reverted changes from 3875 (#3875)

## [64.4.5] - 2024-10-24
### Fixed
- Custom images where also added while empty, causing an error in the scout upload. Now only adding custom images if images are present (#3877)

## [64.4.4] - 2024-10-24
### Fixed
- Orders are connected to their cases (#3884)

## [64.4.3] - 2024-10-24
### Changed
- Removed sendmail-container (#3873)

## [64.4.2] - 2024-10-24
### Changed
- Update pydantic qcmetrics (#3875)

## [64.4.1] - 2024-10-24
### Changed
- Update Pydantic for Taxprofiler (#3872)

## [64.4.0] - 2024-10-23
### Added
- Option to specify order types that an application is applicable for (#3856)

## [64.3.3] - 2024-10-23
### Fixed
- Applications/order_type endpoint renamed (#3879)

## [64.3.2] - 2024-10-23
### Fixed
- The filter_delivery_files method does not manipulate the list indices (#3880)

## [64.3.1] - 2024-10-22
### Added
- Add(bam delivery message) (#3876)

## [64.3.0] - 2024-10-22
### Added
- Endpoint function `get_application_order_types` in `cg/server/endpoints/applications.py` (#3864)
- Error handler for endpoint in `cg/server/endpoints/error_handler.py` (#3864)
- Aplication web service that returns the response to the endpoint in `cg/services/application/service.py` (#3864)
- ApplicationResponse model (#3864)
- Join application order query function `_get_join_application_ordertype_query` in `cg/store/base.py` (#3864)
- CRUD function `link_order_types_to_application`. to create `OrderTypeApplication` entries (create) (#3864)
- CRUF function `get_active_applications_by_order_type` (read) (#3864)
- Status filter module `cg/store/filters/status_ordertype_application_filters.py` for OrderTypeApplication table and one filter function (#3864)
- Attribute `order_types` to the `Appliacation` model in the database (#3864)
- Attribute `application` to the `OrderTypeApplication` model in the database (#3864)
- Tests for the filter function (#3864)
- Test for the CRUD (read) function (#3864)
- Fixtures (#3864)
- Store helpers function (#3864)

## [64.2.2] - 2024-10-22
### Changed
- Update Pydantic for Tomte and RNAFusion (#3852)

## [64.2.1] - 2024-10-22
### Fixed
- Changed call from mip_analysis_api to analysis_api: bugfix for mip-rna (#3871)
- Remove in place manipulation for tag list: bugfix for balsamic and mip-dna (cases with multiple samples) (#3871)

## [64.2.0] - 2024-10-21
### Fixed
- The `software_versions.yml` has been updated to `nf_core_pipeline_software_mqc_versions.yml` (#3240)

## [64.1.2] - 2024-10-21
### Added
- Declare None instead of empty custom images (#3867)

## [64.1.1] - 2024-10-21
### Fixed
- Correct function call to is_suitable_for_genotype_upload (#3866)

## [64.1.0] - 2024-10-21
### Added
- Scout upload for raredisease (#3591)
### Changed
- Unified scout upload for balsamic, rnafusion, raredisease and mip-dna using inherited functions (#3591)

## [64.0.4] - 2024-10-18
### Fixed
- Fix(raise error when sample not found) (#3860)

## [64.0.3] - 2024-10-18
### Changed
- Feat(deliver raw data files for single samples) (#3855)

## [64.0.2] - 2024-10-17
### Added
- Alembic migration script (#3858)
### Changed
- Type of attributes of `PacbioSampleSequencingMetrics` and `PacbioSequencingRun` removing `None` from datatypes (#3858)

## [64.0.1] - 2024-10-17
### Added
- Upload of raredisease cases to genotype (#3784)
### Changed
- Add _mip suffix to mip related genotype functions (#3784)

## [64.0.0] - 2024-10-17
### Changed
- Refactor(rename workflow fastq to rawdata) (#3849)

## [63.7.0] - 2024-10-17
### Added
- Cli command function `post_process_all_runs` in `cg/cli/post_process/post_process.py`. (#3845)
- Utils functions and a model to get and filter the runs to post-process in `cg/cli/post_process/utils.py` (#3845)
- Tests and fixtures for these utils functions (#3845)
- Abstract service family ` RunNamesService` with the child `PacbioRunNamesService` in charge of generating sequencing run names (#3845)
- Tests and fixtures for this new service (#3845)
- New property `run_names_services` in the `CGConfig` class to access the run names service from the config (#3845)
- New check function `is_run_processed` defined abstractly in the post-processing class and in implemented in the Pacbio child class that checks if a run has been post-processed (#3845)

## [63.6.2] - 2024-10-16
### Changed
- Refactor(naming of services) (#3850)

## [63.6.1] - 2024-10-16
### Changed
- Fix genome build hg19 as default for raredisease analysis (#3851)

## [63.6.0] - 2024-10-16
### Added
- OrderTypeApplication table (#3844)

## [63.5.15] - 2024-10-16
### Changed
- Update Pydantic models for MIP (#3848)

## [63.5.14] - 2024-10-15
### Changed
- Decompression SLURM QOS to high (#3836)

## [63.5.13] - 2024-10-14
### Changed
- Filtering on ticket id is done in the Order table (#3833)

## [63.5.12] - 2024-10-14
### Fixed
- Fix(no delivery files check) (#3822)

## [63.5.11] - 2024-10-14
### Added
- Add(fields to pacbio sample) (#3826)

## [63.5.10] - 2024-10-14
### Fixed
- Cascading properties from the devices project (#3823)

## [63.5.9] - 2024-10-14
### Fixed
- Fix(post processing when samples missing) (#3839)

## [63.5.8] - 2024-10-10
### Fixed
- Fix(set case priority research bug) (#3830)

## [63.5.7] - 2024-10-10
### Added
- Add a check in `get_slurm_qos_for_case` to test if a case has only control samples. If this is True, the priority for the case is set to express. (#3816)

## [63.5.6] - 2024-10-10
### Fixed
- Hifi yield displayed for Pacbio sample metrics (#3829)

## [63.5.5] - 2024-10-10
### Changed
- Update model for invoice (#3820)

## [63.5.4] - 2024-10-10
### Changed
- Do not use fields in GConfig (#3824)

## [63.5.3] - 2024-10-09
### Added
- Support for uploading new orderform for OrderType.MICROBIAL_FASTQ (#3777)

## [63.5.2] - 2024-10-09
### Changed
- Update RNAFusion model (#3812)

## [63.5.1] - 2024-10-09
### Changed
- Update Pydantic model for CGConfig (#3808)

## [63.5.0] - 2024-10-08
### Added
- CLI command for cleaning out the /analysis/cases directory (#3284)

## [63.4.1] - 2024-10-08
### Fixed
- Fix - Suppress warnings raised in docker build (#3814)

## [63.4.0] - 2024-10-07
### Added
- View for PacbioSampleRunMetrics (#3809)
- View for PacbioSequencingRun (#3809)

## [63.3.4] - 2024-10-07
### Fixed
- Lower case b:s in Pacbio database models (#3813)

## [63.3.3] - 2024-10-07
### Changed
- Reduced the log level of several compress related commands (#3810)

## [63.3.2] - 2024-10-04
### Added
- Additional condition in post-processing flow for Illumina that checks if the sample has any reads in the lane (#3799)

## [63.3.1] - 2024-10-03
### Fixed
- Fastqs are removed if the potential spring already exists in the K data lake (#3807)

## [63.3.0] - 2024-10-03
### Changed
- Pacbio runs are expected to be barcoded. (#3754)

## [63.2.28] - 2024-10-01
### Fixed
- Mip-rna JSON orders are allowed. (#3793)

## [63.2.27] - 2024-10-01
### Changed
- Raredisease multiQC processing is now raredisease-specific. (#3783)

## [63.2.26] - 2024-09-30
### Added
- Upload of the tomte rna case to the related dna under report section: "rna_delivery_report"/"RNA Delivery Report" (#3782)

## [63.2.25] - 2024-09-30
### Added
- CHILDHYPOTONIA to GenePanelMasterList (#3789)

## [63.2.24] - 2024-09-30
### Changed
- Changed AND to OR in file check (#3791)

## [63.2.23] - 2024-09-27
### Added
- Scout gene panel file path into Raredisease params.yaml (#3779)

## [63.2.22] - 2024-09-26
### Changed
- Improve delivery report pytests (second attempt) (#3776)

## [63.2.21] - 2024-09-26
### Added
- Cg workflow raredisease config case forces gene panel generation (#3772)
### Changed
- Allow hg19 as input for raredisease managed variants (#3772)

## [63.2.20] - 2024-09-26
### Fixed
- Revert "Improve delivery report pytests" (#3774)

## [63.2.19] - 2024-09-26
### Changed
- Removed meta class dependency from the delivery reports (#3631)
- Updated delivery report pytests (#3631)
- Added delivery report pytests for all supported workflows (#3631)
- Some method have been renamed (#3631)
- Removed mocked delivery report related APIs (#3631)

## [63.2.18] - 2024-09-26
### Changed
- Reverts the commit in PR #3689 (#3689)

## [63.2.17] - 2024-09-26
### Fixed
- Fix error in deliver files (#3764)

## [63.2.16] - 2024-09-25
### Added
- Add nextflow workflow stub-run option for tower runs (#3763)
### Changed
- Removed log option for nextflow workflow start and run commands to keep option number under 13 (#3763)

## [63.2.15] - 2024-09-25
### Changed
- Update actions (#3766)

## [63.2.14] - 2024-09-24
### Added
- Loading omics files, rna_genome_build, variant outlier to scout for tomte analyses (#3678)
### Changed
- Move get_genome_build into utils (#3678)
### Fixed
- Use tags instead of hard-coded string for scout tags in upload (#3678)

## [63.2.13] - 2024-09-23
### Added
- Get_related_samples (#3691)
- Get_related_cases (#3691)

## [63.2.12] - 2024-09-23
### Added
- Ngs-bits sex check to raredisease (#3752)

## [63.2.11] - 2024-09-19
### Added
- Registry entry for taxprofiler (#3742)

## [63.2.10] - 2024-09-19
### Fixed
- Fix(delivery files empty bug) (#3747)

## [63.2.9] - 2024-09-19
### Fixed
- Naming of sample and pool filtering based on customers (#3739)

## [63.2.8] - 2024-09-18
### Added
- Add(questions to issue template) (#3700)

## [63.2.7] - 2024-09-18
### Changed
- Return 0 instead of None if price is 0 (#3744)

## [63.2.6] - 2024-09-18
### Added
- Pacbio order submitter (#3743)
- Pacbio order submitter added to the registry (#3743)

## [63.2.5] - 2024-09-18
### Added
- StorePacBioOrderService (#3732)
- Fixtures and tests (#3732)
### Changed
- Moved fixtures to own modules (#3732)

## [63.2.4] - 2024-09-18
### Added
- Add(pacbio run validator) (#3738)

## [63.2.3] - 2024-09-17
### Changed
- Refactor(validate file transfer) (#3737)

## [63.2.2] - 2024-09-17
### Added
- Add decompressor (#3734)

## [63.2.1] - 2024-09-17
### Changed
- Remove pacbio filetransfer validation service (#3735)

## [63.2.0] - 2024-09-17
### Changed
- Renamed workflow fastq to raw-data (#3708)

## [63.1.4] - 2024-09-17
### Changed
- Updated Flask-cors (#3726)

## [63.1.3] - 2024-09-16
### Added
- Validation service for Pacbio orders (#3731)

## [63.1.2] - 2024-09-16
### Added
- Add pacbio order sample (#3733)

## [63.1.1] - 2024-09-16
### Added
- Add(bam delivery support) (#3721)

## [63.1.0] - 2024-09-16
### Changed
- The is_delivered column in Order is renamed to is_open with values flipped. (#3570)

## [63.0.13] - 2024-09-16
### Added
- `OrderType.PACBIO_LONG_READ = "pacbio-long-read"` in `cg/models/orders/constants.py` (#3725)

## [63.0.12] - 2024-09-16
### Added
- Add(post processing completed file) (#3727)

## [63.0.11] - 2024-09-16
### Changed
- Updated Chrypthography (#3724)

## [63.0.10] - 2024-09-13
### Added
- Add(microbial fastq order submitter) (#3701)

## [63.0.9] - 2024-09-12
### Fixed
- Revert accidental commit (#3717)

## [63.0.8] - 2024-09-12
### Changed
- :)

## [63.0.7] - 2024-09-12
### Fixed
- Fix(rsync name to tb api) (#3715)

## [63.0.6] - 2024-09-12
### Fixed
- Fix clinical delivery call (#3713)

## [63.0.5] - 2024-09-11
### Added
- Cg workflow config-case raredisease command will run managed-variants for raredisease (#3697)
- Skip_germlinecnvcaller (dependant on WES or WGS) and vcfanno_extra_resources (passing the managed-variant export from scout) are added to the params file (#3697)
### Changed
- Managed-variants are extracted based on the genome build from statusDB and not hardcoded at hg19 (#3697)

## [63.0.4] - 2024-09-11
### Added
- Add local genomes parameter for raredisease (#3703)

## [63.0.3] - 2024-09-11
### Added
- Pedigree check in raredisease QC: parent_error_ped_check (#3687)
### Changed
- MEDIAN_TARGET_COVERAGE threshold to >25 (#3687)

## [63.0.2] - 2024-09-11
### Changed
- Small fix (#3707)

## [63.0.1] - 2024-09-10
### Fixed
- Fix delete folder (#3705)

## [63.0.0] - 2024-09-10
### Changed
- Feat(new delivery flow) (#3598)

## [62.2.16] - 2024-09-10
### Added
- Storing of a manifest.json file for all nextflow-based pipelines (#3696)

## [62.2.15] - 2024-09-09
### Changed
- Remove deprecated dir (#3672)

## [62.2.14] - 2024-09-05
### Changed
- Change contact (#3690)

## [62.2.13] - 2024-09-04
### Fixed
- Reverted changes from earlier PRs. (#3689)

## [62.2.12] - 2024-09-04
### Changed
- Analyses by cust000 are sent to TB with is_hidden set to True. (#3677)

## [62.2.11] - 2024-09-04
### Changed
- Removed unused `Sample` properties `is_internal/external_neagtive_control`. (#3685)

## [62.2.10] - 2024-09-04
### Fixed
- Fix names of alembic scripts (#3686)

## [62.2.9] - 2024-09-04
### Added
- Test for counting reads of negative controls. (#3684)

## [62.2.8] - 2024-09-04
### Added
- Check to store all fastq files for negative control samples. (#3681)

## [62.2.7] - 2024-09-04
### Added
- Condition to account for all reads for negative control samples regardless of q30. (#3682)

## [62.2.6] - 2024-09-03
### Added
- Check for q30 when calculating Sample.reads (#3680)
- Tests for when the q30 of a lane is below the threshold for the sequencer type (#3680)

## [62.2.5] - 2024-09-03
### Changed
- Replace `osticket` with `freshdesk` (#3668)

## [62.2.4] - 2024-09-02
### Added
- Add capture_kit filter to Sample table in StatusDB. (#3675)

## [62.2.3] - 2024-09-02
### Changed
- Remove pkg_resource use for invoice and delivery report (#3431)

## [62.2.2] - 2024-09-02
### Changed
- Address comments from PacBio dev branch (#3575)

## [62.2.1] - 2024-08-29
### Fixed
- Default value if sequencing_started_at is not available (#3661)

## [62.2.0] - 2024-08-28
### Added
- Added property `is_negative_control` to `Sample` model. (#3300)
- Defined a mutant specific `store-available` function that calls `run_qc_and_fail_analyses()` (#3300)
- `run_qc_and_fail_analyses()` performs qc on a case, generates a qc_report file, adds qc summary to the comment on the analyses on trailblazer and sets analyses that fail QC as failed on Trailblazer. (#3300)
- CLI `run-qc` command to manually run QC on case and generate qc_report file. (#3300)
### Changed
- `MockLimsApi` to have more functionalities for testing. (#3300)

## [62.1.11] - 2024-08-27
### Fixed
- Order validation is performed before submission. (#3644)

## [62.1.10] - 2024-08-27
### Added
- Create trailblazer analysis with workflow id (#3645)

## [62.1.9] - 2024-08-26
### Changed
- Feat(rsync) Remove -t flag for sars-cov (#3641)

## [62.1.8] - 2024-08-26
### Fixed
- Return is_tumour instead of tumour in samples_in_collaboration (#3637)

## [62.1.7] - 2024-08-26
### Fixed
- Ordered_at is updated for each submitted order (#3629)

## [62.1.6] - 2024-08-21
### Fixed
- Fix id conversion (#3606)

## [62.1.5] - 2024-08-19
### Added
- Add missing user endpoints (#3596)

## [62.1.4] - 2024-08-19
### Changed
- Refactor flow cells endpoint (#3549)

## [62.1.3] - 2024-08-19
### Changed
- Extract user endpoints (#3547)

## [62.1.2] - 2024-08-19
### Changed
- Extract analyses endpoints (#3546)

## [62.1.1] - 2024-08-19
### Changed
- Refactor(submitters) (#3574)

## [62.1.0] - 2024-08-15
### Added
- CLI command `cg post-process run <run-name>` which currently works with PacBio SMRT cells but will work for any run in the future (#3453)
- Abstract interfaces for the classes described in the diagram above, suitable for overriding with the proper classes for each device (#3453)
- Classes for the PacBio post-processing (#3453)
- CRUD functions to create and read PacBio DB entries (#3453)
- Util functions (#3453)
- Test functions, fixtures and fixture files (#3453)
### Changed
- Function `store_fastq_path_in_housekeeper` in housekeeper modified into `create_bundle_and_add_file_with_tags` so that it works in a more general way (not only for fastqs) (#3453)

## [62.0.60] - 2024-08-15
### Fixed
- Prevent GENS files being provided to Balsamic CLI for hg38 (#3568)

## [62.0.59] - 2024-08-15
### Changed
- Removed -p flag for rsync (#3566)

## [62.0.58] - 2024-08-14
### Fixed
- Renamed `hi_fi_reads` to `hifi_reads` (#3564)
- Renamed `hi_fi_yield` to `hifi_yield` (#3564)
- Renamed `run_started_at` to `started_at` (#3564)
- Renamed `run_completed_at` to `completed_at` (#3564)
- Renamed `Productive_ZMWS` to `productive_zmws` (#3564)

## [62.0.57] - 2024-08-14
### Added
- Add(microbialfastqsample orderin) (#3553)

## [62.0.56] - 2024-08-14
### Added
- Add parameter same_mapped_as_cram to raredisease parameters file (as not taken-in properly in config file) (#3558)

## [62.0.55] - 2024-08-14
### Changed
- Ensure samples in case are RNA (#3550)

## [62.0.54] - 2024-08-14
### Added
- Add gens upload for raredisease (#3539)
- Add clinical-delivery upload for raredisease (#3540)

## [62.0.53] - 2024-08-13
### Changed
- Update paths to match pipeline (#3559)

## [62.0.52] - 2024-08-13
### Added
- Add d4 format (#3560)

## [62.0.51] - 2024-08-13
### Fixed
- Correct error handling when fetching non-existent flow cells (#3557)

## [62.0.50] - 2024-08-13
### Added
- Error handler when we do not have an entry in statusdb (#3556)

## [62.0.49] - 2024-08-12
### Changed
- Refactor(error handling crud) (#3551)

## [62.0.48] - 2024-08-09
### Changed
- Extract pool endpoints (#3544)

## [62.0.47] - 2024-08-09
### Changed
- Extract order endpoints (#3514)

## [62.0.46] - 2024-08-09
### Changed
- Extract sample endpoints (#3513)

## [62.0.45] - 2024-08-09
### Changed
- Extract application endpoints (#3517)

## [62.0.44] - 2024-08-08
### Changed
- Extract case endpoints (#3515)

## [62.0.43] - 2024-08-08
### Changed
- Sort imports to resolve conflicts in pacbio dev branch (#3542)

## [62.0.42] - 2024-08-08
### Fixed
- Fix internal (#3541)

## [62.0.41] - 2024-08-08
### Added
- Add loqus DB upload for raredisease (#3516)

## [62.0.40] - 2024-08-08
### Changed
- Removed Pandas from FOHM API (#3365)
- Use CSV and Pydatic to read and validate content (#3365)

## [62.0.39] - 2024-08-08
### Fixed
- Fix invalid microbial order form fixture (#3531)

## [62.0.38] - 2024-08-07
### Added
- Raredisease protected tags (#3526)
### Changed
- Rnafusion hermes defined clinical-delivery tags (#3526)

## [62.0.37] - 2024-08-07
### Added
- Add sequencing times for PacBio run (#3530)

## [62.0.36] - 2024-08-07
### Changed
- Add information to be shown in TB comment for QC checks (sample id, sample name and threshold) (#3529)

## [62.0.35] - 2024-08-06
### Fixed
- Fix priority and status sample fields (#3525)

## [62.0.34] - 2024-08-06
### Added
- Add missing application data to response from collaborator samples endpoint (#3521)

## [62.0.33] - 2024-08-06
### Changed
- Use sample id instead of case id for rnafusion (#3069)

## [62.0.32] - 2024-08-06
### Added
- Add force store comment (#3500)

## [62.0.31] - 2024-08-05
### Changed
- Updated setuptools (#3441)

## [62.0.30] - 2024-08-05
### Changed
- Hide cancelled samples from customers (#3510)

## [62.0.29] - 2024-08-05
### Changed
- Refactor cancel action (#3507)

## [62.0.28] - 2024-08-05
### Changed
- Update zipp (#3442)

## [62.0.27] - 2024-08-05
### Added
- Add default value to cancelled column (#3511)

## [62.0.26] - 2024-08-02
### Added
- Add is_cancelled field (#3506)

## [62.0.25] - 2024-07-29
### Added
- Add analysis comment column (#3468)

## [62.0.24] - 2024-07-29
### Added
- Add pacbio sample metrics model (#3474)

## [62.0.23] - 2024-07-29
### Added
- Add delivery report Raredisease (#3459)

## [62.0.22] - 2024-07-29
### Added
- Add Chanjo2 API (#3450)

## [62.0.21] - 2024-07-24
### Added
- Two test functions (#3461)
- TXT extension constant (#3461)

## [62.0.20] - 2024-07-24
### Changed
- Feat - add second SMRTcell fixture and files (#3443)

## [62.0.19] - 2024-07-23
### Added
- Add `Bug` label to bug report template (#3457)

## [62.0.18] - 2024-07-23
### Fixed
- Added `about` section in the heading in the bug report issue template. (#3455)

## [62.0.17] - 2024-07-22
### Changed
- Refactor - PacBio metric parser (#3449)

## [62.0.16] - 2024-07-22
### Changed
- Remove sequencing QC calculations in /orders endpoint (#3403)

## [62.0.15] - 2024-07-18
### Changed
- Fixed percentage calculations in productivity metrics (#3447)

## [62.0.14] - 2024-07-18
### Added
- Add fastq analysis delivery message (#3446)

## [62.0.13] - 2024-07-18
### Fixed
- Fix microsalt delivery message content (#3445)

## [62.0.12] - 2024-07-18
### Fixed
- Fix(collect sequencing times) (#3438)

## [62.0.11] - 2024-07-17
### Added
- Metrics model (#3436)
- Function to parse specifically the smrtlink-datasets file in the metrics parser (#3436)
- Constants for metrics names (#3436)
- Fixture for parsed metrics and fixture file (#3436)
### Changed
- Merged `_parse_report` and `parse_attributes_to_model` methods of the metrics parser into one, called `parse_report_to_model`. (#3436)
- Updated tests of these functions (#3436)
### Fixed
- Implemented `TypeVar` from the `typing` module to better type-hint the different metrics classes, so just typing the parent class (BaseModel from Pydantic) (#3436)

## [62.0.10] - 2024-07-15
### Changed
- Cleanup(renaming and moving files and classes illumina) (#3428)

## [62.0.9] - 2024-07-15
### Added
- Field validators (#3425)
- Fixtures and tests (#3425)
### Changed
- Added validate upon assignment in DTO config (#3425)

## [62.0.8] - 2024-07-11
### Fixed
- Fix(parsing runparameter) (#3424)

## [62.0.7] - 2024-07-11
### Added
- Add foreingkey constraint to samplerunmetrics and sample (#3423)

## [62.0.6] - 2024-07-10
### Changed
- Remove deprecated statusdb views (#3421)

## [62.0.5] - 2024-07-10
### Fixed
- Fix wrong commit (#3422)

## [62.0.4] - 2024-07-10
### Added
- Add sample foreign key

## [62.0.3] - 2024-07-10
### Fixed
- Fix columns in new models admin view (#3420)

## [62.0.2] - 2024-07-10
### Added
- Pydantic model for the polymerase metrics (#3415)
- Constants with the attribute names of the raw-data report file (#3415)
- Fixtures for raw-data report file and productivity metrics object (#3415)
- Function in `utils` to divide by 1000 and keep only one decimal for changing bases into kilobases and its unit test (#3415)
### Changed
- Updated test of metrics parser to work with polymerase model (#3415)
### Fixed
- Metric attributes needed in kb instead of bases were changed to float and validated before assignment. Their value will only have one decimal figure (as in the SMRTlnk web interface). (#3415)
- Removed unused report file fixture (#3415)

## [62.0.1] - 2024-07-10
### Fixed
- Fix(percent q30 scaling) (#3419)

## [62.0.0] - 2024-07-10
### Changed
- Re-route flow to illumina device tables. (#3349)

## [61.4.7] - 2024-07-09
### Added
- Pydantic model for the productivity metrics (#3412)
- Constants with the attribute names of the loading report file (#3412)
- Fixtures for loading report file and productivity metrics object (#3412)
### Changed
- Updated test of metrics parser to work with productivity model (#3412)

## [61.4.6] - 2024-07-08
### Fixed
- Bumped certifi from 2023.7.22 to 2024.7.4 (#3413)

## [61.4.5] - 2024-07-08
### Added
- Pydantic model for the control metrics (#3409)
- Constants with the attribute names of the control report file (#3409)
- Unit test for percent function (#3409)
- Fixtures for control report file and metrics object (#3409)
### Changed
- Moved the percent field validator to a separate function to be more DRY (#3409)
- Updated test of metrics parser to work with control model (#3409)

## [61.4.4] - 2024-07-08
### Changed
- 3184 replace parameter yes with skip confirmation (#3401)

## [61.4.3] - 2024-07-08
### Added
- Constants for file names and keywords in JSON metrics file to be parsed (#3308)
- Class `MetricsParser` which parses HiFi metrics but also expandable to any other PacBio metrics (#3308)
- Pydantic model `HiFiMetrics` (#3308)
- Fixtures and tests (#3308)

## [61.4.2] - 2024-07-08
### Added
- Add PON to balsamic delivery reports (#3402)

## [61.4.1] - 2024-07-05
### Changed
- Log level decreased for `get_cases` in `scoutapi.py` (#3400)
- Log level decreased for `hk_alignment_files` in `clean.py` (#3400)

## [61.4.0] - 2024-07-04
### Added
- Add sequencing QC CLI command (#3287)

## [61.3.6] - 2024-07-04
### Fixed
- Fix(col type yield) (#3398)

## [61.3.5] - 2024-07-04
### Fixed
- Fix(downsample help cmd) (#3394)

## [61.3.4] - 2024-07-04
### Fixed
- Revert "Revert gens force flag (#3375)(patch)" (#3389)

## [61.3.3] - 2024-07-04
### Added
- Sentieon common license server address (#3386)
- Balsamics sentieon license path (#3386)

## [61.3.2] - 2024-07-02
### Added
- Tests (#3383)
### Changed
- Refactor master list usage (#3383)

## [61.3.1] - 2024-07-01
### Added
- Apptag version to apptag description and ordering sections (#3382)
### Changed
- Some delivery report text (#3382)

## [61.3.0] - 2024-07-01
### Added
- Support for getting deliveries for cases with delivery type analysis. (#3362)

## [61.2.12] - 2024-06-28
### Added
- Add(metrics dto) (#3374)

## [61.2.11] - 2024-06-28
### Changed
- Remove force flag from gens upload (#3375)

## [61.2.10] - 2024-06-27
### Fixed
- If not provided, the region_code and original_lab_address are populated for the provided region and original_lab. (#3367)

## [61.2.9] - 2024-06-27
### Added
- Passes `--force` flag to `gens load sample` (#3322)
- Prints stderr from `gens load sample` as a warning (#3322)

## [61.2.8] - 2024-06-26
### Added
- New exceptions `SampleSheetFormatError` and `SampleSheetContentError` (#3355)
### Changed
- Replaced all occurrences of `SampleSheetError` for either `SampleSheetFormatError` and `SampleSheetContentError` (#3355)
- Fixed the try-except clauses to perform different conditions for the two different exceptions (#3355)
- Sample sheet Error only used in Nextflow code renamed to `NfSampleSheetError` (#3355)

## [61.2.7] - 2024-06-25
### Changed
- Default is to archive 300 spring files every 20th minute. (#3359)

## [61.2.6] - 2024-06-24
### Changed
- Archive 500 files every 20 minutes between 22-08. (#3356)

## [61.2.5] - 2024-06-24
### Changed
- Use specific run paths instead of self.path (#3353)

## [61.2.4] - 2024-06-19
### Added
- POETRY_REQUESTS_TIMEOUT environment variable for PyPi publishing github action (#3352)

## [61.2.3] - 2024-06-19
### Added
- App_config.py containing the BaseSettings class AppConfig (#3350)
### Changed
- Keys in the app.config are now in snake_case to follow the normal use of BaseSettings (#3350)
### Fixed
- Unused config entries are removed (#3350)

## [61.2.2] - 2024-06-19
### Added
- Store, store-available and store-housekeeper commands for raredisease with template file bundle for deliverables (#3128)

## [61.2.1] - 2024-06-18
### Changed
- Updated Urllib3 (#3346)

## [61.2.0] - 2024-06-18
### Added
- Retry functionality (#3328)
- Error handling for the one existing method (#3328)
### Changed
- Requests are now submitted using a session (#3328)
- The session is configured upon instantiation (#3328)

## [61.1.6] - 2024-06-17
### Added
- Method `store_illumina_data_in_housekeeper` in `IlluminaPostProcessingService`. (#3325)
### Changed
- Renamed method `store_illumina_flow_cell_data` to ` store_illumina_data_in_status_db` for clarity (#3325)

## [61.1.5] - 2024-06-17
### Changed
- The sample's customer's archive location is used when retrieving files. (#3330)

## [61.1.4] - 2024-06-17
### Changed
- Force storage of incomplete analyses (#3340)

## [61.1.3] - 2024-06-13
### Fixed
- Cases in trailblazer do not get any additional statuses inferred. (#3343)

## [61.1.2] - 2024-06-13
### Added
- Functions to filter IlluminaSampleSequencingMetrics by run id, sample internal id and lane (filter function and in CRUD) (#3333)
- Functions to filter IlluminaSequencingRun by run id (filter function and in CRUD) (#3333)
- Fixture `store_with_illumina_sequencing_data` (#3333)
- Store helper functions to add and ensure IlluminaFlowCells, IlluminaSequencingRuns and IlluminaSampleSequencingMetrics (#3333)
### Changed
- Test for IlluminaFlowCell filters to use correct store fixture (#3333)
- Illumina post-processing tests (#3333)
- Functions to store IlluminaSampleSequencingMetrics in post-processing service and CRUD, to align more with SRP (#3333)

## [61.1.1] - 2024-06-13
### Changed
- Refactor(flow cells dir) (#3336)

## [61.1.0] - 2024-06-13
### Changed
- Feature(always update chanjo samples) (#3337)

## [61.0.4] - 2024-06-12
### Added
- Add(mip analysis upload workaround) (#3332)

## [61.0.3] - 2024-06-12
### Added
- `sample_id` in the error message for when the fastq files for a sample cannot be delivered since they are not present in the sample bundle. (#3335)

## [61.0.2] - 2024-06-12
### Added
- Added a constant in cg/cli/utils.py that is a dictionary with the value of the terminal size -10. (#3315)
- In `@click.group()` decorators, added the parameter `context_settings=CLICK_CONTEXT_SETTINGS`. The command will therefore display a number of character equal to terminal size - 10. (#3315)
### Fixed
- Truncated characters in `--help` command. (#3315)

## [61.0.1] - 2024-06-11
### Added
- Add(support assignment undetermined reads to sample in new flow) (#3331)

## [61.0.0] - 2024-06-11
### Changed
- Refactor(demultiplexing cli commands) (#3326)

## [60.9.8] - 2024-06-10
### Added
- Add DV200 and Reception QC metrics to delivery report (#3270)

## [60.9.7] - 2024-06-10
### Changed
- An error is raised when the latest analysis has not completed in the nf-tower storing (#3309)

## [60.9.6] - 2024-06-10
### Added
- Freshdesk client (#3317)
- Create ticket method (#3317)

## [60.9.5] - 2024-06-10
### Changed
- Refactor(rename flow cell in demux api) (#3313)

## [60.9.4] - 2024-06-10
### Changed
- 1604 version 18 accepted form RML and Fluffy (#3321)

## [60.9.3] - 2024-06-03
### Changed
- Refacto(flow cell dir data pt1) (#3310)

## [60.9.2] - 2024-05-30
### Fixed
- Revert "add admin view of new tables" (#3305)

## [60.9.1] - 2024-05-30
### Added
- Reference path added to target_bed parameter (#3303)

## [60.9.0] - 2024-05-30
### Added
- Add admin view of new tables (#3265)

## [60.8.26] - 2024-05-30
### Added
- Add(illumina device store flow) (#3293)

## [60.8.25] - 2024-05-30
### Added
- Add Pacbio sequencing run model (#3298)

## [60.8.24] - 2024-05-30
### Changed
- Issue templates to agile (#3302)

## [60.8.23] - 2024-05-29
### Added
- Params file to file deliverables for tomte (#3296)

## [60.8.22] - 2024-05-29
### Changed
- Default behaviour for NF workflows to write dynamic variables in the params file. Params file takes precedence over config files and avoid configuration errors in the workflow due to incomplete propagation of variables. (#3295)

## [60.8.21] - 2024-05-29
### Changed
- Replaces hard-coded directory with microsalt root dir (#3294)

## [60.8.20] - 2024-05-28
### Changed
- DEFAULT_CAPTURE_KIT = twistexomecomprehensive_10.2_hg19_design.bed (#3292)

## [60.8.19] - 2024-05-28
### Added
- Add(functionality for accurate time stamps for flow cell) (#3290)

## [60.8.18] - 2024-05-27
### Added
- SMRT cell SQLAlchemy model (#3275)
- Alembic migration (#3275)

## [60.8.17] - 2024-05-27
### Changed
- Rename service (#3285)

## [60.8.16] - 2024-05-27
### Added
- Add and remove(columns illumina sequencing run) (#3286)

## [60.8.15] - 2024-05-27
### Fixed
- Fix serialization of enum (#3281)

## [60.8.14] - 2024-05-27
### Added
- Add(aggregate parsing functions) (#3274)

## [60.8.13] - 2024-05-27
### Added
- Add sequencing QC field to case model (#3279)

## [60.8.12] - 2024-05-27
### Changed
- Run parameters always looked for in flow cell dir (#3278)

## [60.8.11] - 2024-05-27
### Added
- Support sending exomes cases in raredisease (#3232)
### Changed
- Default target bed file for both MIP and raredisease updated to "twistexomerefseq_10.2_hg19_design.bed" (#3232)

## [60.8.10] - 2024-05-27
### Fixed
- Fix(change coltype illumina sequencing run) (#3277)

## [60.8.9] - 2024-05-24
### Added
- Add(yield parsing to bclconvert metrics parser) (#3271) (pa)ch=

## [60.8.8] - 2024-05-23
### Changed
- Updated pymysql (#3269)

## [60.8.7] - 2024-05-23
### Changed
- Update requests (#3268)

## [60.8.6] - 2024-05-23
### Changed
- Refactor(demux post processing run parameters) (#3263)

## [60.8.5] - 2024-05-23
### Added
- Add(yield columns to new sample run metrics) (#3264)

## [60.8.4] - 2024-05-23
### Changed
- Prepend date alembic scripts (#3266)

## [60.8.3] - 2024-05-22
### Changed
- Removes the short flag "-d" in the DRY_RUN option in cg/constants/constants.py (#3244)
- In test files, "-d" was changed to "--dry-run". (#3244)

## [60.8.2] - 2024-05-22
### Changed
- Refactor(demux flow for new flow cell model pt2) (#3256)

## [60.8.1] - 2024-05-22
### Added
- Add autoincrement for run device (#3257)

## [60.8.0] - 2024-05-22
### Added
- Relationships between device -> run_metrics -> sample_run_metrics (#3246)
- Property to access devices from samples (#3246)
- Property to access samples from device (#3246)

## [60.7.31] - 2024-05-21
### Added
- "multiqc-html" tag to "MIP_DNA_ANALYSIS_CASE_TAGS. (#3259)

## [60.7.30] - 2024-05-20
### Changed
- Remove obsolete panels SEXDET, SEXDIF from the DSD Scout bundle (#3247)

## [60.7.29] - 2024-05-20
### Changed
- Pytest action runs on 8-core machins (#3242)

## [60.7.28] - 2024-05-20
### Changed
- Remove dead code (#3248)

## [60.7.27] - 2024-05-20
### Changed
- Refctor(sequencing metrics parser) (#3241)

## [60.7.26] - 2024-05-20
### Changed
- Block FFPE samples from Loqusdb upload (#3215)

## [60.7.25] - 2024-05-20
### Added
- IlluminaFlowCellDevice model (#3239)
- Alembic migration (#3239)

## [60.7.24] - 2024-05-17
### Added
- Add(illumina run metrics table) (#3235)

## [60.7.23] - 2024-05-17
### Fixed
- Path is converted to list of paths in the Microsalt cleaning. (#3225)

## [60.7.22] - 2024-05-16
### Fixed
- Case name in cg add case is only allowed to contain letters, digits and dashes. (#3237)

## [60.7.21] - 2024-05-16
### Changed
- Use beefier test runner (#3233)

## [60.7.20] - 2024-05-16
### Added
- Add RIN thresholds for Rnafusion & Tomte delivery reports (#3203)

## [60.7.19] - 2024-05-16
### Added
- Add(validate pacbio transfer cli) (#3226)

## [60.7.18] - 2024-05-16
### Added
- Add(illumina samle run metrics) (#3229)

## [60.7.17] - 2024-05-15
### Changed
- Hide Taxprofiler per lane metrics (#3227)

## [60.7.16] - 2024-05-15
### Added
- Sex check as part of cg workflow raredisease metrics-deliver case (#3192)

## [60.7.15] - 2024-05-15
### Fixed
- Remove unnecessary arguments when running taxprofiler (#3230)

## [60.7.14] - 2024-05-15
### Added
- `intenal_id` column to `RunDevice` model (#3221)
- New alembic migration with the changes (#3221)

## [60.7.13] - 2024-05-14
### Added
- Foreign key to `run_metrics` (#3220)

## [60.7.12] - 2024-05-14
### Added
- Add constraint of primary key to device tables (#3224)

## [60.7.11] - 2024-05-14
### Fixed
- Cases failing sequencing QC are counted in the order summary. (#3198)

## [60.7.10] - 2024-05-13
### Fixed
- Fix bug in config-case (#3217)

## [60.7.9] - 2024-05-13
### Changed
- Made dry-run as a constant and referring the files to it (#3204)

## [60.7.8] - 2024-05-13
### Changed
- Update (#3219)

## [60.7.7] - 2024-05-13
### Fixed
- Fix(downsample api) (#3210)

## [60.7.6] - 2024-05-13
### Changed
- Rename fastq file service (#3216)

## [60.7.5] - 2024-05-08
### Added
- Add( tables for new prod tech) (#3202)

## [60.7.4] - 2024-05-07
### Changed
- Id and ticket_id are searchable fields in Order. (#3209)

## [60.7.3] - 2024-05-07
### Changed
- Updated Jinja2 to 3.1.4 (#3208)

## [60.7.2] - 2024-05-07
### Changed
- Drops the delivery table (#3079)

## [60.7.1] - 2024-05-07
### Changed
- Updated werkzeug to 3.0.3 (#3207)

## [60.7.0] - 2024-05-06
### Added
- New functions in `ExternalAPI` and their tests (#2892)
### Changed
- Modified the `ExternalAPI` to be more modular and readable, renaming internal functions with preceding `_`. (#2892)
- Made `dry_run`, `ticket`, `customer` and `force` attributes fo the class so that they are not passed around all intermediate functions. (#2892)
- Moved static functions to more appropriate modules (md5 function to checksum and `are_all_fastq_valid` to utils (#2892)
### Fixed
- Method `ExternalAPI.add_transfer_to_housekeeper` so that it includes files to bundles and process every sample independently (#2892)

## [60.6.3] - 2024-05-03
### Changed
- Update deplyoment instructions (#3200)

## [60.6.2] - 2024-05-03
### Fixed
- Revert "Fix analysis started at assignment (#3195)" #3199

## [60.6.1] - 2024-05-02
### Fixed
- Fix analysis started at assignment (#3195)

## [60.6.0] - 2024-05-02
### Changed
- Allows orders with data_analyses="tomte" to be ordered (#3119)

## [60.5.0] - 2024-05-02
### Added
- CLI command for retrieving a sample (#3190)
- CLI command for retrieving a case (#3190)
- CLI command for retrieving an order (#3190)

## [60.4.11] - 2024-04-29
### Changed
- Feat(jasen) Add Jasen to analysis options (#3189)

## [60.4.10] - 2024-04-29
### Changed
- Only include analyses ready to be delivered in order message (#3191)

## [60.4.9] - 2024-04-29
### Added
- Tag `run-parameters` (#3047)
- Function `add_run_parameters_file_to_housekeeper` in `cg/meta/demultiplex/housekeeper_storage_functions.py` (#3047)
- Test for `add_run_parameters_file_to_housekeeper` (#3047)
- A check in the test of `finish flow-cell` that verifies that the run parameters file has been added to Housekeeper. (#3047)

## [60.4.8] - 2024-04-29
### Changed
- Updated tomte deliverables (#3177)

## [60.4.7] - 2024-04-29
### Added
- Add taxprofiler delivery report (#3188)

## [60.4.6] - 2024-04-29
### Fixed
- Tomte config-case to work with several samples (#3185)

## [60.4.5] - 2024-04-26
### Changed
- Remove remnant sars-cov-2 workflow occurence in order table (Fix #3179) (#3186)

## [60.4.4] - 2024-04-26
### Fixed
- Fix markdown format of CONTRIBUTING.md (#3173)

## [60.4.3] - 2024-04-25
### Added
- Data_archive_location is no shown in the admin-view (#3180)
- Reordered som columns (#3180)

## [60.4.2] - 2024-04-25
### Changed
- Reordered fixtures, moved from contest to fixture_plugins (#3176)
- Removed unwanted fixtures, replaced usages for updated fixtures when applicable (#3176)

## [60.4.1] - 2024-04-25
### Added
- Conditional parameters for tomte: gene panel, genome and tissue (#3112)

## [60.4.0] - 2024-04-25
### Added
- Sequencing quality check service (#2886)
- Sequencing quality checks, dependent on preparation category, workflow, and priority (#2886)

## [60.3.2] - 2024-04-25
### Changed
- Clean tests and constants from bcl2fastq (#3174)

## [60.3.1] - 2024-04-24
### Changed
- Removed `FlowCellSampleBcl2Fastq` and its usages. (#3171)
- Rename `FlowCellBclConvertSample` to `FlowCellSample` (#3171)
- Update of usages of abstract class `FlowCellSample` (#3171)
- The translation of the sample sheet no longer checks if the sample sheet is Bcl2Fastq. If it is not in the correct format, it will just fail sample validation. The checking passed from using `_is_sample_sheet_from_flow_cell_translatable` to directly calling `_are_necessary_files_in_flow_cell`. (#3171)
- This makes the methods `_is_sample_sheet_bcl2fastq` and `_is_sample_sheet_from_flow_cell_translatable` unused, so they were removed (#3171)
- Removed Bcl2Fastq-specific index functions and constants in `cg/apps/demultiplex/sample_sheet/index.py`. (#3171)
- Removed function `get_sample_type_from_content` as we only. use one flow cell sample type (BCLConvert) (#3171)
- Changed function `get_flow_cell_samples_from_content` so that it no longer receives a sample type as parameter, it uses BCLConvert always (#3171)
- Removed unused models `SampleSheetBcl2Fastq` and `SampleSheetBCLConvert` (#3171)
- Modified all functions that took a sample type as parameter to use only BCLConvert (#3171)
- Removed test functions and fixtures related to removed classes and functions (#3171)

## [60.3.0] - 2024-04-24
### Added
- Add delivery report for Tomte (#3154)

## [60.2.13] - 2024-04-24
### Added
- Jinja macros to delivery report (#3118)
### Changed
- Delivery report HTML (#3118)

## [60.2.12] - 2024-04-23
### Changed
- Replace redirect (#3172)

## [60.2.11] - 2024-04-23
### Changed
- The function `get_flow_cell_samples` from LIMS API no longer receives the FlowCellSample model, as it uses `FlowCellBclConvertSample` only. (#3164)
- This causes `_get_flow_cell` and `get_or_create_sample_sheet` in the sample sheet API not need the bclconvert as parameter, so it is removed. (#3164)
- Remove `bcl_converter` from parameter of the `FlowCellDirectoryData` model, as it uses only BCLConvert. (#3164)
### Fixed
- All usages of above functions, removing bclconvert parameter (#3164)

## [60.2.10] - 2024-04-23
### Changed
- Improve CLI dockerfile (#3166)

## [60.2.9] - 2024-04-23
### Changed
- Archiving default was halved to 100 files. (#3162)

## [60.2.8] - 2024-04-23
### Changed
- Bypass LIMS for delivery report (#3153)

## [60.2.7] - 2024-04-22
### Added
- A fixture environment consisting of a store, a context and a Post-processing API based on the seven canonical flow cells for demultiplexing (2 HiSeqX, 2HiSeq2500, 2 NovaSeq6000 and 1 NovaSeqX) The new fixtures are: (#3160)
- `updated_store_with_demultiplexed_samples` (#3160)
- `updated_demultiplex_context` (#3160)
- `seven_canonical_flow_cells` (#3160)
- `seven_canonical_flow_cells_selected_sample_ids` (#3160)
- Files for the new demultiplexed flow cell fixtures (#3160)
### Changed
- Removed all patterns involving `Unaligned` in `cg/meta/demultiplex/utils.py` (#3160)
- Moved some fixtures to fixture pluggins (#3160)

## [60.2.6] - 2024-04-22
### Changed
- Feat(jasen) Add jasen workflow without subcommands (#3053)

## [60.2.5] - 2024-04-22
### Changed
- Update Gunicorn (#3156)

## [60.2.4] - 2024-04-22
### Fixed
- Changed to handle Case instead of dict in add_transfer_to_housekeeper (#3117)

## [60.2.3] - 2024-04-19
### Fixed
- Handle all orders being filtered away (#3155)

## [60.2.2] - 2024-04-19
### Fixed
- Filtering orders on Balsamic only matches on startswith. (#3149)

## [60.2.1] - 2024-04-19
### Changed
- Update idna (#3146)

## [60.2.0] - 2024-04-18
### Added
- Cg workflow raredisease metrics-deliver case_id (#2924)

## [60.1.6] - 2024-04-18
### Changed
- The invoice template specifies AG as contact person. (#3151)

## [60.1.5] - 2024-04-18
### Changed
- Moved the limit to take place just before iteration (#3150)

## [60.1.4] - 2024-04-17
### Changed
- Removed directories `models` and `parsers` in `cg/apps/sequencing_metrics_parser`. The `bcl_convert` modules were moved one folder up, at the same level as the API, so now we have a flat structure. (#3137)
- Renamed `BclConvertMetricsParser` to `MetricsParser` (#3137)
- Renamed `BclConvertQualityMetrics` to `SequencingQualityMetrics` (#3137)
- Renamed `BclConvertDemuxMetrics` to `DemuxMetrics` (#3137)
- Moved function `get_flow_cell_id` to `g/utils/flow_cell.py` so that it is accessible to all the code in a nice dependence tree (#3137)
- Removed bcl2fastq demultiplexed flow cell fixture and its data (#3137)

## [60.1.3] - 2024-04-17
### Changed
- MIP cases started are limited to 33 (#3147)
- Balsamic cases started are limited to 21 (#3147)

## [60.1.2] - 2024-04-17
### Fixed
- Validation in the order delivery message includes checks for uploaded_at and correct workflow. (#3144)

## [60.1.1] - 2024-04-17
### Changed
- Return workflow_limitations as part of the applications endpoint (#3142)

## [60.1.0] - 2024-04-17
### Changed
- Removed the bcl converter parameter from all the finish functions (#3132)
- Deleted functions, modules, tests and fixtures of sequencing metric parsing of bcl2fastq (#3132)
- Moved the logic for parsing BCLConvert sequencing metrics directly to the sequencing metrics API in `cg/apps/sequencing_metrics_parser/api.py` (before this API evaluated the bcl converter and called the respective parser). (#3132)
- Moved and refactored the tests for BCLConvert sequencing metrics parsing to the API tests (#3132)
- Moved some fixtures to fixture plugins (#3132)

## [60.0.0] - 2024-04-16
### Changed
- Removed `bcl2fastq` sbatch command (#3127)
- Made all demultiplexing jobs use BCLConvert in the DRAGEN (#3127)
- Removed unused tests and fixtures (#3127)

## [59.25.8] - 2024-04-16
### Changed
- Show private key in order table (#3126)
- Order.is_delivered can be toggled (#3126)

## [59.25.7] - 2024-04-16
### Changed
- Rnafusion delivery report accreditation. Now accredited for a specific tag and input amount. (#3105)

## [59.25.6] - 2024-04-16
### Changed
- The analysis ids which the order delivery message was generated for are included in the response. (#3131)

## [59.25.5] - 2024-04-16
### Changed
- Removed `SampleSheetCreatorBcl2Fastq`. Moved all logic of `SampleSheetCreatorBCLConvert` to `SampleSheetCreator`. (#3116)
- Removed sample sheet creator factory. (#3116)
- Removed functions to discard single-index samples (only bcl2fastq) (#3116)
- Removed valid index path (#3116)
- Removed tests and fixtures (#3116)

## [59.25.4] - 2024-04-15
### Added
- Added delivery of files for tomte (#3123)

## [59.25.3] - 2024-04-15
### Changed
- Removed methods `_validate_bcl2fastq` and `_validate_sample_sheet_is_correct_type` of class `SampleSheetValidator` (#3111)
- Removed method `_validate_bcl_convert` method, included its logic in `validate_sample_sheet_from_content`. (#3111)
- Removed tests (#3111)

## [59.25.2] - 2024-04-15
### Added
- Add admin view for orders (#3125)

## [59.25.1] - 2024-04-15
### Fixed
- Fix(encrypton failing) (#3104)

## [59.25.0] - 2024-04-15
### Added
- Caesar delivery for taxprofiler (#3108)

## [59.24.2] - 2024-04-15
### Changed
- Updated linters (#3124)

## [59.24.1] - 2024-04-15
### Changed
- Updated dnspython (#3122)

## [59.24.0] - 2024-04-15
### Changed
- Parameter `bcl_converter` od sample sheet API function `get_or_create_sample_sheet` from mandatory to optional set to `None` by default. (#3107)

## [59.23.0] - 2024-04-15
### Changed
- Mutant has order form 2184.9 instead of 2184.8 (#3081)

## [59.22.7] - 2024-04-15
### Fixed
- Order.delivered changed to order.is_delivered (#3113)

## [59.22.6] - 2024-04-11
### Fixed
- Return type matches signature (#3106)

## [59.22.5] - 2024-04-10
### Added
- Added panel POI to panel combo DSD. (#3098)

## [59.22.4] - 2024-04-10
### Added
- `--exome `argument to balsamic for samples with wes application tags (#3061)

## [59.22.3] - 2024-04-10
### Added
- Tests for the new functionality. (#3088)
### Changed
- The validation of the sample sheet is now bcl-converter-specific. The commands like demultiplex all and create all sample sheets use `BCLConverter` by default, so `bcl2fastq` sample sheets will fail validation in the automation. If cought in the creation phase, the sample sheets will be updated to a `BCLConvert` sample sheet. If caught in the demultiplexing phase, the demultiplexing will fail after the slurm job has been submitted so the error can be easily tracked. (#3088)
- `bcl2fastq` sample sheets can still be created, validated and used in demultiplexing by explicitly specifying the converter as a CLI parameter. (#3088)
### Fixed
- The `SampleSheetAPI` attribute `bcl_converter` was removed and the bcl converter of the flow cell is used instead to avoid ambiguity. (#3088)

## [59.22.2] - 2024-04-10
### Fixed
- Patch order table (#3103)

## [59.22.1] - 2024-04-09
### Added
- Include is_delivered (#3101)

## [59.22.0] - 2024-04-09
### Changed
- Filter orders by delivered (#3096)

## [59.21.0] - 2024-04-09
### Added
- Add endpoint for automatically updating order delivery status (#3097)

## [59.20.7] - 2024-04-09
### Fixed
- Fix incorrect down revision (#3099)

## [59.20.6] - 2024-04-09
### Added
- Add endpoint for marking order as delivered (#3095)

## [59.20.5] - 2024-04-09
### Changed
- Tomte included in the workflow enum in the order table (#3091)

## [59.20.4] - 2024-04-08
### Added
- Start and start-available commands for raredisease workflow (#3093)

## [59.20.3] - 2024-04-08
### Changed
- Downsampled samples inherit the original sample's received_at and prepared_at. (#3089)

## [59.20.2] - 2024-04-08
### Fixed
- Both completed and delivered counts are reported in the order status summary. (#3090)

## [59.20.1] - 2024-04-04
### Changed
- Flowcell.samples is now a property instead of a backref (#3063)
- Sample.flowcells -> Sample.flow_cells (#3063)
- Sample.flow_cells is now a property instead of a backref (#3063)
- Removed code linking samples and flow cells via the link table (#3063)

## [59.20.0] - 2024-04-04
### Added
- Report-deliver, store-housekeeper, store and store-available commands for tomte (#3084)

## [59.19.0] - 2024-04-03
### Added
- CLI command `cg demultiplex samplesheet translate_sample_sheet` (#3062)
- Functions in the SampleSheetAPI (#3062)
- `_is_sample_sheet_from_flow_cell_translatable` (#3062)
- `_replace_sample_header` (#3062)
- `translate_sample_sheet` (endpoint) (#3062)
- Tests for the 3 new functions (#3062)
- Fixtures (#3062)

## [59.18.2] - 2024-04-02
### Added
- Metrics-deliver subcommand for tomte (#3078)

## [59.18.1] - 2024-04-02
### Fixed
- Fixed path to be correct (#3080)
- Simplified some functions (#3080)

## [59.18.0] - 2024-03-27
### Changed
- Improve order summary service (#3050)

## [59.17.3] - 2024-03-27
### Fixed
- Get_job_status uses GET (#3071)

## [59.17.2] - 2024-03-26
### Added
- Start and start-available subcommands for tomte (#3056)

## [59.17.1] - 2024-03-26
### Changed
- Order_id was dropped from Case (#3067)

## [59.17.0] - 2024-03-25
### Added
- Cg workflow taxprofiler store-available (#3059)
- Tomte_mock_config. The test_cli_run.py was pointing to raredisease mock config. (#3059)
### Changed
- They were three fixtures with the name mock_config, renamed them to raredisease_mock_config, rnafusion_mock_config and taxprofiler_mock_config (#3059)

## [59.16.0] - 2024-03-25
### Changed
- Associate rsync jobs with analysis (#3045)

## [59.15.5] - 2024-03-21
### Fixed
- MIP-RNA delivery messages raises an error (#3054)

## [59.15.4] - 2024-03-21
### Changed
- Update variable usage in delivery messages (#3044)
### Fixed
- Typos in delivery messages (#3044)

## [59.15.3] - 2024-03-21
### Added
- Cg workflow taxprofiler store case_id (#3038)

## [59.15.2] - 2024-03-21
### Added
- Run subcommand for tomte workflow (#3055)

## [59.15.1] - 2024-03-20
### Added
- Config case command for tomte workflow (#3046)
### Changed
- Generalized config case methods and pytests across nf workflows (#3046)

## [59.15.0] - 2024-03-19
### Added
- Add new delivery service (#3029)

## [59.14.13] - 2024-03-19
### Changed
- Remove dead code (#3051)

## [59.14.12] - 2024-03-19
### Fixed
- Fix sample views (#3049)

## [59.14.11] - 2024-03-19
### Changed
- Adjust down revision (#3048)

## [59.14.10] - 2024-03-19
### Changed
- Remove unused sample columns (#3041)

## [59.14.9] - 2024-03-19
### Added
- Tomte as workflow in application limitations table (#3043)

## [59.14.8] - 2024-03-18
### Added
- Added tomte as workflow without any subcommands (#3034)

## [59.14.7] - 2024-03-18
### Added
- Delivery of multiqc inftermediate files for rnafusion (#2919)

## [59.14.6] - 2024-03-18
### Changed
- Pipeline to workflow in applicationLimitations for database and end-point. (#3000)

## [59.14.5] - 2024-03-18
### Fixed
- VWGNXTR001 also have delivery message support (#3040)

## [59.14.4] - 2024-03-18
### Added
- Add tomte as workflow to StatusDB (#3037)

## [59.14.3] - 2024-03-15
### Added
- Add raredisease run case (#2732)

## [59.14.2] - 2024-03-14
### Fixed
- Fixed function invoked by parametrised workflow pytests (#3036)

## [59.14.1] - 2024-03-14
### Added
- Add(cg store qc-metrics) (#3017)

## [59.14.0] - 2024-03-14
### Added
- Cg workflow taxprofiler store-housekeeper case_id (#3015)

## [59.13.0] - 2024-03-13
### Fixed
- Unified the fastq concatenation (#3028)

## [59.12.0] - 2024-03-11
### Added
- Endpoint for getting the delivery message for an order (#3030)

## [59.11.2] - 2024-03-11
### Changed
- Use snake case and remove aliases in nf workflow parameters (#3032)

## [59.11.1] - 2024-03-10
### Fixed
- Fix nextflow pipelines bug with cluster options and prio (#3031)

## [59.11.0] - 2024-03-08
### Added
- Endpoint for fetching delivery message for a set of cases (#3026)

## [59.10.8] - 2024-03-06
### Fixed
- Cases added via the CLI gets connected to the order related to the ticket_id. (#3023)

## [59.10.7] - 2024-03-06
### Fixed
- Fix(add sample cli) (#3019)

## [59.10.6] - 2024-03-05
### Changed
- Update cryptography (#3001)

## [59.10.5] - 2024-03-04
### Added
- Add raredisease config (#2725)

## [59.10.4] - 2024-03-04
### Added
- Add httpstatus instead of int (#3016)

## [59.10.3] - 2024-03-04
### Added
- Add(arnoldapi functionality create case) (#3009)

## [59.10.2] - 2024-03-04
### Fixed
- Fix order search filter (#3014)

## [59.10.1] - 2024-03-04
### Changed
- Order_id is removed from the response body (#3011)

## [59.10.0] - 2024-03-04
### Added
- Support searching orders (#3012)

## [59.9.1] - 2024-03-04
### Changed
- Always include order status summary (#3013)

## [59.9.0] - 2024-03-01
### Added
- Support sorting orders (#3010)

## [59.8.0] - 2024-02-29
### Added
- Add order pagination (#3004)

## [59.7.3] - 2024-02-29
### Changed
- The analyses' statuses are included when fetching an order (#3003)

## [59.7.2] - 2024-02-29
### Fixed
- If there is an order with the given ticket_id, an error is raised upon order submission. (#3006)

## [59.7.1] - 2024-02-29
### Changed
- Researcher ID changed from 3, to whatever is provided in the .env file (#3005)

## [59.7.0] - 2024-02-29
### Added
- Cg workflow taxprofiler report-deliver case_id (#2912)

## [59.6.3] - 2024-02-29
### Changed
- Refactor(collect qc metrics) (#3007)

## [59.6.2] - 2024-02-29
### Added
- Add(collect qc metrics meta api) (#2990)

## [59.6.1] - 2024-02-29
### Added
- Add (Balsamic) cluster config option (#3002)

## [59.6.0] - 2024-02-28
### Added
- Add order status service (#2965)

## [59.5.9] - 2024-02-28
### Changed
- Refactor pipeline, and pipeline_version to workflow in database analysis table (#2980)

## [59.5.8] - 2024-02-28
### Fixed
- Fixtures use valid app tags (#2985)

## [59.5.7] - 2024-02-28
### Fixed
- Downsampled cases are added to the same order as the latest order for the original case. (#2991)

## [59.5.6] - 2024-02-27
### Changed
- Rm `FILTER_` from filter object attributes. Harmonize to filter instead of get in filter functions. (#2979)

## [59.5.5] - 2024-02-27
### Fixed
- Flowcell.status now has the default "ondisk" again (#2989)

## [59.5.4] - 2024-02-27
### Fixed
- Removed all import from cg in the alembic scripts (#2986)

## [59.5.3] - 2024-02-26
### Added
- Add(janusapi) (#2977)

## [59.5.2] - 2024-02-26
### Added
- Add(arnoldapi) (#2978)

## [59.5.1] - 2024-02-26
### Fixed
- Revert refactoring of the delivery API (#2988)

## [59.5.0] - 2024-02-26
### Changed
- Trailblazer analyses are now created with order_ids. (#2929)

## [59.4.7] - 2024-02-26
### Fixed
- Patch delivery bug (#2984)

## [59.4.6] - 2024-02-26
### Changed
- Updated models.py according to the five steps listed [here](https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#migrating-an-existing-mapping) (#2961)
- Changed some tuple constants to be Enums (#2961)

## [59.4.5] - 2024-02-23
### Fixed
- Use cases with the specified ticket_id for matching with a new order. (#2976)

## [59.4.4] - 2024-02-22
### Fixed
- Fix deletion without confirmation of other sample sheets (#2973)

## [59.4.3] - 2024-02-22
### Changed
- Refactor delivery api (#2796)

## [59.4.2] - 2024-02-22
### Fixed
- Checks that a flow cell directory is indeed a directory before trying to create a sample sheet for it (#2971)

## [59.4.1] - 2024-02-22
### Changed
- Concatenate fastq files for microsalt deliveries (#2951)

## [59.4.0] - 2024-02-22
### Added
- A new class `SampleSheetValidator` with the endpoint function `validate_sample_sheet` which will be the new function to validate sample sheets. (#2958)
- A new class `OverrideCyclesValidator` with the endpoint function `validate_sample` which will validate if the override cycles for a single sample is correct. It is called for each sample inside the `SampleSheetValidator`. (#2958)
- A new SampleSheetAPI that takes the logic away from the CLI commands. (#2958)
- Tests and fixtures for new functions (#2958)
### Changed
- Took the validation away from `cg/apps/demultiplex/sample_sheet/read_sample_sheet.py` into the validator class. (#2958)
- The sample sheet is now validated every time is fetched (for creation and demultiplexing). (#2958)
### Fixed
- Tests for CLI command, parametrised with new fixtures (#2958)

## [59.3.1] - 2024-02-21
### Added
- Add deliverable tag to metrics deliver (#2964)

## [59.3.0] - 2024-02-21
### Added
- Order_case are created upon order submission. (#2952)

## [59.2.1] - 2024-02-20
### Fixed
- Fix microsalt reruns picking up old jobs (#2967)

## [59.2.0] - 2024-02-20
### Added
- OrderCase table (#2960)

## [59.1.1] - 2024-02-19
### Changed
- All usages of the `like` methods are replaced by `contains` (#2959)

## [59.1.0] - 2024-02-19
### Added
- Vcf delivery tags (#2943)

## [59.0.0] - 2024-02-19
### Changed
- Refactor to workflow in tb api (#2932)

## [58.1.9] - 2024-02-15
### Fixed
- Python-multipart updated to 0.0.9 (#2945)

## [58.1.8] - 2024-02-15
### Added
- Add CopyComplete.txt file creation in BackupAPI (#2913)

## [58.1.7] - 2024-02-14
### Fixed
- Change hard-coded paths in bcl2fastq demux script to match the file structure (#2950)

## [58.1.6] - 2024-02-14
### Changed
- Removes unused columns from Illumina sample sheet (#2934)
- Update fixtures (#2934)

## [58.1.5] - 2024-02-13
### Added
- A new entry to the Header section of the sample sheet with the name of the index settings used (#2931)

## [58.1.4] - 2024-02-12
### Fixed
- Dict keys updated as well (#2933)

## [58.1.3] - 2024-02-12
### Changed
- Dry run for Balsamic run analysis (#2925)

## [58.1.2] - 2024-02-12
### Changed
- Scout files logs for delivery report & remove outdated UDF access (#2923)

## [58.1.1] - 2024-02-12
### Added
- Upload RNA alignment CRAM file to Scout (#2920)

## [58.1.0] - 2024-02-12
### Changed
- CGConfig.demultiplexed_flow_cells_dir to CGConfig.illumina_novaseq_demultiplexed_flow_cells_directory (#2824)
- Bound directories for bcl2fastq slurm jobs (#2824)
- CGConfig.flow_cells_dir to CGConfig.illumina_novaseq_flow_cells_directory (#2824)
- Renamed a lot of fixtures to match this (#2824)

## [58.0.0] - 2024-02-12
### Changed
- Refactor pipeline to workflow config (#2926)

## [57.0.7] - 2024-02-09
### Added
- Added support to fetch panel info from development samples in LIMS (#2928)

## [57.0.6] - 2024-02-09
### Changed
- Improve token validation error logs (#2927)

## [57.0.5] - 2024-02-09
### Changed
- Improve log message

## [57.0.4] - 2024-02-08
### Fixed
- Fastq orders get subject_id set on sample level. (#2888)

## [57.0.3] - 2024-02-08
### Changed
- Rnafusion/taxprofiler workflow: create and use nextflow config by default (#2915)

## [57.0.2] - 2024-02-08
### Fixed
- Use workflow instead of order type when creating orders. (#2917)

## [57.0.1] - 2024-02-08
### Fixed
- Restored file deliverables path (#2921)

## [57.0.0] - 2024-02-08
### Changed
- Refactor to workflow in CLI call (#2911)

## [56.3.9] - 2024-02-07
### Changed
- Turn off slurm scout upload (#2918)

## [56.3.8] - 2024-02-07
### Added
- Upload scout cases via slurm (#2895)

## [56.3.7] - 2024-02-07
### Added
- Add bug report template (#2910)

## [56.3.6] - 2024-02-07
### Fixed
- Fastapi, cryptography and starlette have all been bumped. (#2907)

## [56.3.5] - 2024-02-06
### Fixed
- Fix metrics path (#2909)

## [56.3.4] - 2024-02-06
### Added
- Endpoint for fetching an order via order_id (#2898)

## [56.3.3] - 2024-02-06
### Changed
- Refactors `pipeline` into `workflow` for functions and CLI (#2894)

## [56.3.2] - 2024-02-05
### Fixed
- Fix microsalt job ids path (#2901)

## [56.3.1] - 2024-02-05
### Added
- Include microsalt report path in summary (#2899)

## [56.3.0] - 2024-02-05
### Changed
- DataDelivery is set to NO_DELIVERY for every downsampled case. (#2900)

## [56.2.8] - 2024-02-05
### Fixed
- Patch microsalt jobs tracking (#2897)

## [56.2.7] - 2024-02-01
### Changed
- Refactor Pipeline to workflow for enum (#2885)
- Remove casting to str (#2885)

## [56.2.6] - 2024-01-31
### Changed
- Update toml (#2891)

## [56.2.5] - 2024-01-31
### Fixed
- The imports to Housekeeper store point to the correct location (#2889)

## [56.2.4] - 2024-01-31
### Fixed
- Fix(find downsample fastq files) (#2878)

## [56.2.3] - 2024-01-31
### Changed
- Remove sars-cov-2 from pipeline constant (#2883)

## [56.2.2] - 2024-01-31
### Added
- Support for filtering orders on workflow. (#2881)

## [56.2.1] - 2024-01-30
### Changed
- Update Black (#2872)

## [56.2.0] - 2024-01-30
### Changed
- (feat taxprofiler) Add metrics-deliver (#2701)

## [56.1.0] - 2024-01-30
### Added
- Create order entry when an order is placed (#2876)

## [56.0.2] - 2024-01-30
### Changed
- Use `get_create_version()` instead of `last_version()` (#2880)
- Removed error raise (#2880)
- Renamed `get_create_version` to `get_or_create_version` (#2880)

## [56.0.1] - 2024-01-30
### Added
- Pipeline column to the order table. (#2870)
- Order-Customer relationship (#2870)

## [56.0.0] - 2024-01-29
### Changed
- Pipeline constant sars-cov-2 to mutant (#2835)
- Change existing entries in database (#2835)

## [55.6.2] - 2024-01-29
### Fixed
- Fix invalid call in upload flow (#2875)

## [55.6.1] - 2024-01-26
### Added
- Add caesar upload job to analysis in trailblazer (#2869)

## [55.6.0] - 2024-01-25
### Added
- Endpoint for fetching database entries from the new orders table. (#2868)

## [55.5.1] - 2024-01-25
### Added
- Function to calculate barcode mismatches for index 2 (#2867)
- Test for new function (#2867)
### Changed
- Renamed previous hamming distance for indexes to only index (#2867)
- Parametrised tests (#2867)

## [55.5.0] - 2024-01-24
### Added
- Order table (#2866)
- Column in case table with a foreign key constraint to the order id. (#2866)

## [55.4.11] - 2024-01-24
### Changed
- Changed debug statements for warnings (#2865)
### Fixed
- The check now fails if **all** samples are missing. So if only one sample is missing, it will clean the existing sample bundles (#2865)
- A Try-except will catch individual bundles `HousekeeperBundleVersionMissingError` (#2865)

## [55.4.10] - 2024-01-23
### Changed
- Remove Corehandler (#2859)
- Refactor Store (#2859)
- Move base.py (#2859)

## [55.4.9] - 2024-01-23
### Fixed
- Use jinja2 >= v.3.1.3 (#2862)

## [55.4.8] - 2024-01-23
### Changed
- Posts are not part of the Payload classes. (#2855)

## [55.4.7] - 2024-01-23
### Changed
- Refactor statushandler into CRUD (#2858)

## [55.4.6] - 2024-01-22
### Changed
- Update Balsamic API (Balsamic v13 release) (#2657)

## [55.4.5] - 2024-01-22
### Changed
- Refactor find basic data into CRUD (#2844)

## [55.4.4] - 2024-01-18
### Fixed
- The archive handlers are instantiated once per batch instead of once per file. (#2850)

## [55.4.3] - 2024-01-18
### Changed
- Remove constants for symbols (#2854)

## [55.4.2] - 2024-01-18
### Fixed
- Revert the check inside the method `validate_sample_sheet` of the class `FlowCellDirectoryData` that compares the sample sheet type extracted from the sample sheet itself and the bcl converter of the `FlowCellDirectoryData`. (#2853)

## [55.4.1] - 2024-01-17
### Added
- Add statina link in delivery message (#2849)

## [55.4.0] - 2024-01-17
### Added
- Add delivery message endpoint (#2845)

## [55.3.10] - 2024-01-16
### Added
- Directory `flow_cells_broken` to distinguish the files from working flow cells from flow cells missing files (required by some tests) (#2847)
### Changed
- Renamed several fixtures (#2847)
### Fixed
- Removed fixtures and files for flow cells 180522_A00689_0200_BHLCKNCCXY and 170407_A00689_0209_BHHKVCALXX (#2847)

## [55.3.9] - 2024-01-16
### Fixed
- Wrap last_sequenced_at as string in metadata, if present. (#2846)

## [55.3.8] - 2024-01-16
### Changed
- Removes `BclConverter.DRAGEN` and changes it with `BclConverter.BCLCONVERT` (#2843)

## [55.3.7] - 2024-01-16
### Changed
- Refactor read handler to CRUD (#2831)

## [55.3.6] - 2024-01-16
### Added
- Raw sample file `tests/fixtures/apps/demultiplexing/flow_cells/190927_A00689_0069_BHLYWYDSXX/HLYWYDSXX_bcl2fastq_raw.json` with anonymised names and projects (#2841)
### Changed
- Renamed `novaseq_6000_pre_1_5_kits_lims_samples` and `novaseq_6000_post_1_5_kits_lims_samples` to explicitly include the bcl converter in their name (#2841)
### Fixed
- Removed fixture `lims_novaseq_6000_bcl2fastq_samples`, replaced usages with `novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples`. (#2841)
- Removed fixture `lims_novaseq_bcl_convert_samples`, replaced usages with `novaseq_x_lims_samples` (#2841)
- Removed paths to lims sample files that were used only once. Instantiated Path in the fixture where they were used instead. (#2841)

## [55.3.5] - 2024-01-15
### Added
- Create fastq analysis in trailblazer (#2833)

## [55.3.4] - 2024-01-15
### Changed
- Temp fix for tracking microsalt cases in tb (#2840)

## [55.3.3] - 2024-01-12
### Changed
- Update coveralls action (#2836)

## [55.3.2] - 2024-01-12
### Added
- Add reads qc to non microbial samples in microsalt (#2834)

## [55.3.1] - 2024-01-12
### Added
- Add qc for non microbial samples in microsalt (#2825)

## [55.3.0] - 2024-01-12
### Added
- CLI command for deleting retrieved Spring files. (#2815)

## [55.2.3] - 2024-01-12
### Changed
- Move delete and update to CRUD namespace (#2808)

## [55.2.2] - 2024-01-11
### Added
- Add microsalt upload command (#2823)

## [55.2.1] - 2024-01-11
### Changed
- Deliver the correct microsalt files (#2800)

## [55.2.0] - 2024-01-11
### Added
- Fixture plugin modules with fixtures in the new folder `tests/fixture_plugins/` with the following structure: (#2816)
### Changed
- Moved demultiplexing and timestamp fixtures from `conftest.py` to separate modules in the new fixture plugin directory. (#2816)

## [55.1.1] - 2024-01-10
### Changed
- Remove mark_analyses_deleted (#2817)

## [55.1.0] - 2024-01-10
### Added
- Method for checking if the Spring file in a CompressionData object is archived. (#2814)
### Changed
- Compression of Fastq -> Spring is not performed when Spring is archived. (#2814)

## [55.0.0] - 2024-01-09
### Changed
- Remove uploaded to vogue from the database and models (#2810)

## [54.10.7] - 2024-01-09
### Fixed
- Fix missing microsalt jobs (#2813)

## [54.10.6] - 2024-01-09
### Fixed
- New concentration is uploaded to LIMS (#2785)

## [54.10.5] - 2024-01-09
### Changed
- Delivery report mandatory for Scout uploads (#2704)
- Renamed function get_report_accreditation to is_report_accredited (#2704)

## [54.10.4] - 2024-01-08
### Added
- This PR adds a check inside the method `validate_sample_sheet` of the class `FlowCellDirectoryData` that compares the sample sheet type extracted from the sample sheet itself and the bcl converter of the `FlowCellDirectoryData`. If they don't match, it fails the validation and informs this mismatch in the logs as a warning. (#2806)

## [54.10.3] - 2024-01-08
### Added
- Metadata in the archival requests towards DDN/Miria. (#2799)
### Changed
- The archival flow sends one request per file. (#2799)

## [54.10.2] - 2024-01-08
### Changed
- [Commits](https://github.com/paramiko/paramiko/compare/3.3.1...3.4.0) (#2783)
- Dependency-name: paramiko (#2783)

## [54.10.1] - 2024-01-08
### Changed
- Refactor addhandler (#2788)

## [54.10.0] - 2024-01-05
### Added
- OPTIC panel (cust003) to the scout masterlist (#2802)

## [54.9.1] - 2024-01-04
### Changed
- Fix sample name format in DownsampleData class (#2798)

## [54.9.0] - 2024-01-04
### Added
- Test functions for `FlowCellBCLConvertSample` and `FlowCellBcl2FastqSample` classes (#2736)
- Fixtures and fixture files for new flow cell cases (#2736)
### Changed
- Separate the module `cg/apps/demultiplex/sample_sheet/models.py` into sample models (`cg/apps/demultiplex/sample_sheet/sample_models.py`) and sample sheet models (`cg/apps/demultiplex/sample_sheet/sample_sheet_models.py`) for readability. (#2736)
- Made all the sample updating logic part of the FlowCellSample class, moving all the functions in `index.py` that have sample logic to one of the flow cell sample models in `cg/apps/demultiplex/sample_sheet/sample_models.py` (#2736)
- `get_index_pair` -> `separate_indexes` (#2736)
- `update_barcode_mismatch_values_for_sample` -> `update_barcode_mismatches` (#2736)
- `pad_and_reverse_complement_sample_indexes` -> ` _pad_indexes_if_necessary` (#2736)
- `update_indexes_for_samples` -> `process_indexes` (#2736)
- Moved the `IndexSettings` logic from the sample sheet creator to the RunParameters class (#2736)
- Moved all the override cycles and barcode mismatch updating logic from the sample sheet creator to the FlowCellSample models (#2736)
- Removed the index length equality rule from RunParameters (#2736)
- Removed the `bcl_converter` attribute from the FlowCellDirectoryData class, as it can be accessed through the `run_parameters` attribute (#2736)
### Fixed
- Tests and usages that depended of the bcl converter of the flow cell (#2736)

## [54.8.0] - 2024-01-03
### Added
- Check for the ONT "Sequencing finished"-file (#2789)
### Changed
- The directory iteration now uses glob instead if iterdir, to support wildcards in the input (#2789)

## [54.7.0] - 2024-01-03
### Changed
- Added check for any archived spring files related to the case, and if so, a job is launched to retrieve them. (#2674)

## [54.6.1] - 2024-01-02
### Changed
- Parallelise test action (#2794)

## [54.6.0] - 2024-01-02
### Added
- Add automatic quality control of analyses for microbial samples (#2754)

## [54.5.3] - 2023-12-21
### Changed
- Refactor gender to sex (#2780)

## [54.5.2] - 2023-12-20
### Changed
- Added field to hold new concentration field. (#2740)

## [54.5.1] - 2023-12-19
### Changed
- Rename family to case_id in TB (#2777)

## [54.5.0] - 2023-12-18
### Added
- Application.sample_concentration_minimum_cfdna (#2776)
- Application.sample_concentration_maximum_cfdna (#2776)

## [54.4.10] - 2023-12-18
### Fixed
- Fix panel combo bug (#2779)

## [54.4.9] - 2023-12-18
### Changed
- Accept FlowCellError and continue cleaning (#2775)

## [54.4.8] - 2023-12-14
### Changed
- Split run_analysis method in nf_analysis (#2772)

## [54.4.7] - 2023-12-14
### Added
- Workflow protected tags for rnafusion (#2773)

## [54.4.6] - 2023-12-14
### Changed
- Split the ddn_data_flow.py module into three and encapsulated them in a DDN package. (#2766)

## [54.4.5] - 2023-12-14
### Changed
- Remove deprecated code (#2755)

## [54.4.4] - 2023-12-14
### Fixed
- Fix bug causing mip workflow start to fail (#2769)

## [54.4.3] - 2023-12-14
### Changed
- Use general tower binary instead of specifying it as part of the pipeline (#2767)

## [54.4.2] - 2023-12-14
### Changed
- FastqFile model (#2763)
- Gzip read function (#2763)
- Tests (#2763)

## [54.4.1] - 2023-12-13
### Changed
- Set compute environment according the case priority (#2765)

## [54.4.0] - 2023-12-13
### Added
- CLI command which deletes a file at the archive location and in Housekeeper. (#2760)

## [54.3.1] - 2023-12-13
### Changed
- Use constants for rnafusion HK tags instead of strings (#2759)

## [54.3.0] - 2023-12-12
### Added
- Panel `Inherited cancer` to clinical master list (#2761)

## [54.2.1] - 2023-12-11
### Added
- Method `get_managed_variants` to `MipRNAAnalysisAPI` (#2757)
### Changed
- Moved method `write_managed_variants` from `MipDNAAnalysisAPI` to `MipAnalysisAPI` so that it is available also for MipRNA (#2757)

## [54.2.0] - 2023-12-11
### Added
- Scout export manged variants function (#2750)
- CLI cmd to export variants (#2750)
- Tests (#2750)

## [54.1.3] - 2023-12-08
### Fixed
- Map enums to their values. (#2752)

## [54.1.2] - 2023-12-08
### Changed
- Logging on INFO level to logging on WARNING level when readiness checks fail before demultiplexing (#2751)

## [54.1.1] - 2023-12-08
### Changed
- Update Ruff (#2746)

## [54.1.0] - 2023-12-08
### Changed
- Removed `Delete_flow_cell_API` (#2593)
- Removed the `cg demultiplex delete-flow-cell` CLI command (#2593)
- No longer checks for active cases before removing stuff (Does one not always want to restart with new data?) (#2593)

## [54.0.0] - 2023-12-07
### Added
- Fusion VCF file to deliverables (#2621)
- Gene counts file to deliverables (#2621)
- CRAM index files to deliverables (#2621)
- Scout upload of a Rnafusion alignment CRAM file (#2621)
- Swedac logo in delivery report (#2621)
### Changed
- Rnafusion bundle filenames (#2621)
- Replaced deprecated metrics: (#2621)
- 5_3_bias by median_5prime_to_3prime_bias (#2621)
- Reads_aligned by reads_pairs_examined (#2621)
- Updated default parameters (#2621)
- Skip path validation in model (#2621)

## [53.6.0] - 2023-12-07
### Added
- Panel CLI (#2718)
- Test and fixtures (#2718)
### Changed
- Refactored panel functions and gene panel constants (#2718)

## [53.5.4] - 2023-12-06
### Added
- Add panel combo for Oftalmologi as requested by cust002. (#2695)

## [53.5.3] - 2023-12-06
### Added
- PANELAPP-GREEN to run by default (#2700)

## [53.5.2] - 2023-12-06
### Fixed
- A provided limit of a non-positive integer now results in an exit. (#2737)

## [53.5.1] - 2023-12-06
### Changed
- Update black (#2739)

## [53.5.0] - 2023-12-06
### Added
- Method `prepare_output_directory` to both remove and create output directory (#2619)
### Changed
- Output dir creation moved from `start_demultiplexing` to new function `prepare_output_directory` (#2619)
- Method `create_demultiplexing_output_dir` now only takes one argument (#2619)

## [53.4.8] - 2023-12-06
### Added
- Enable delivery of external samples (#2727)

## [53.4.7] - 2023-12-06
### Added
- Class `IndexSettings` to hold settings (#2683)
- Function: `_get_index_settings` to return the correct settings. (#2683)
- Function: `_is_novaseq6000_post_1_5_kit` to check the version of novaseq6000 flow cells (#2683)
- Tests for the three types of NovaSeq flow cells (#2683)
- Fixtures for three new flow cell directories (#2683)
### Changed
- Removed `is_reverse_complement` (#2683)
- Removed `get_hamming_distance_index_2` (#2683)
- Removed `is_reverse_complement_needed` (#2683)
- Removed `get_reagent_kit_version` (#2683)

## [53.4.6] - 2023-12-06
### Changed
- Remove balsamic run-analysis flag from cg (#2723)

## [53.4.5] - 2023-12-06
### Changed
- Increase case id range (#2684)

## [53.4.4] - 2023-12-05
### Changed
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst) (#2714)
- [Commits](https://github.com/pyca/cryptography/compare/41.0.4...41.0.6) (#2714)
- Dependency-name: cryptography (#2714)

## [53.4.3] - 2023-12-05
### Changed
- Files to archive are now filtered already in the SQL query, using the archive location tag. (#2730)

## [53.4.2] - 2023-12-04
### Changed
- Metagenome orders now go via the 1508 sheet (#2734)

## [53.4.1] - 2023-12-04
### Fixed
- Unless otherwise specified, api requests are verified. (#2733)

## [53.4.0] - 2023-12-01
### Added
- CLI command archive-all-non-archived-spring-files which invokes its namesake in the SpringArchiveAPI. (#2345)
- CLI command update-job-statuses which queries any ongoing archivals/retrievals to see if they have finished. (#2345)

## [53.3.0] - 2023-11-30
### Added
- Create application versions via admin ui (#2721)

## [53.2.0] - 2023-11-30
### Changed
- Spring files are now tagged with the customer's archive location in Housekeeper. (#2717)

## [53.1.11] - 2023-11-30
### Added
- `SampleSheetError` to the list of caught exceptions in the cli command `cg demultiplex samplesheet create-all` (#2720)
- A meaningful warning to the log when a sample sheet can't be created (#2720)

## [53.1.10] - 2023-11-30
### Changed
- Do not use `.value` with StrEnum and IntEnums (#2712)
- Use classmethods for mixed type constants, instead of detached constants (#2712)
- Better type safety with single type in Enums (#2712)

## [53.1.9] - 2023-11-30
### Added
- Class `RunParametersHiSeq`, implementing abstract methods from parent. (#2653)
- Constants to parse the elements from the XML file (#2653)
- XMLError exception (#2653)
- Test for new class (#2653)
### Changed
- Moved and renamed function `node_not_found` in `RunParameters` class to `cg/io/xml.py:validate_node_exists` (#2653)
- Replaced RunParametersError exception for XMLError in the validation of the nodes. (#2653)
### Fixed
- Removed unused sample sheets in fixtures (#2653)

## [53.1.8] - 2023-11-29
### Changed
- Answer yes for symmetric cmd (#2715)

## [53.1.7] - 2023-11-28
### Changed
- Answer yes in gpg encrypt and decrypt cmds (#2707)

## [53.1.6] - 2023-11-28
### Changed
- Skip lims sample metadata collection for rnafusion report generation if down sampled (#2705)

## [53.1.5] - 2023-11-28
### Fixed
- Fix fastq tag assignment from spring file (#2710)

## [53.1.4] - 2023-11-27
### Changed
- Get job status endpoint, request and response. (#2692)
- Aliases for camel case responses. (#2692)

## [53.1.3] - 2023-11-27
### Changed
- Refactor to pep 0604 (#2706)

## [53.1.2] - 2023-11-24
### Added
- Assert-function to test content of file (#2708)
### Changed
- Parametrization of post-processing test (#2708)
### Fixed
- Name of fixture (#2708)

## [53.1.1] - 2023-11-24
### Added
- New test for the `panel` function (#2682)

## [53.1.0] - 2023-11-22
### Added
- Add cg nas and encryption dir (#2703)

## [53.0.2] - 2023-11-21
### Added
- Add delivery report to Balsamic-QC workflow (#2689)

## [53.0.1] - 2023-11-21
### Added
- Add Balsamic validated metrics to delivery report (#2688)

## [53.0.0] - 2023-11-20
### Added
- Encryption dir (#2694)
### Changed
- Separate encryption dir for backup retrieval and, encryption and backup archiving. Since retrieval has one more path level than encrypting and archiving. (#2694)

## [52.1.6] - 2023-11-17
### Changed
- Only set has_backup if both encryption key and flow cell have been archived. (#2693)

## [52.1.5] - 2023-11-15
### Added
- Autoinflammation disease (AID) panel to clinical master list - fix https://github.com/Clinical-Genomics/cg/issues/2686 (#2687)

## [52.1.4] - 2023-11-15
### Changed
- Allow 3 running dsmc processes (#2690)

## [52.1.3] - 2023-11-14
### Changed
- Rename family in db (#2670)

## [52.1.2] - 2023-11-10
### Fixed
- Fix(move error handling clean flow cells) (#2678)

## [52.1.1] - 2023-11-10
### Fixed
- Fix(relax clean flow cell criteria) (#2677)

## [52.1.0] - 2023-11-09
### Added
- Support for querying ongoing archivals/retrievals and updating their statuses. (#2319)

## [52.0.11] - 2023-11-09
### Fixed
- Usage of f-strings for parts of the repo. (#2672)

## [52.0.10] - 2023-11-08
### Fixed
- We now import from Pydantic v2 in meta/upload/scout (#2531)

## [52.0.9] - 2023-11-08
### Changed
- Rename family sample model (#2669)

## [52.0.8] - 2023-11-07
### Changed
- Rename family relationships to case (#2666)

## [52.0.7] - 2023-11-07
### Changed
- Remove unused function in Trailblazer API (#2648)

## [52.0.6] - 2023-11-07
### Fixed
- Removed string coercion validators. (#2665)

## [52.0.5] - 2023-11-07
### Fixed
- Fix code smell flagged by sonarcloud (#2667)

## [52.0.4] - 2023-11-07
### Fixed
- Patch views (#2663)

## [52.0.3] - 2023-11-07
### Changed
- Rename Family to Case (#2655)

## [52.0.2] - 2023-11-07
### Changed
- Update patched dependencies (#2662)

## [52.0.1] - 2023-11-07
### Fixed
- Fix toml structure (#2656)

## [52.0.0] - 2023-11-07
### Changed
- Feat(cg downsample) (#2488)

## [51.10.7] - 2023-11-07
### Changed
- Retrieve undetermined fastqs in root for flow cells with flat output (#2659)

## [51.10.6] - 2023-11-07
### Fixed
- Prevent re-analysis to be triggered for cases without new data (#2660)

## [51.10.5] - 2023-11-01
### Changed
- Warning exit codes from the dsmc command no longer raise errors (#2638)

## [51.10.4] - 2023-11-01
### Fixed
- Add_decompressed_fastq_files_to_housekeeper is split into smaller methods. (#2597)

## [51.10.3] - 2023-10-31
### Changed
- Replace hardcoded validation cases (#2645)

## [51.10.2] - 2023-10-31
### Added
- Cli option: `cg workflow raredisease` (#2649)

## [51.10.1] - 2023-10-31
### Fixed
- We check for pending decompressions in the decompress flow. (#2641)

## [51.10.0] - 2023-10-31
### Added
- CLI command to create a manifest file (#2623)
- A check in the `confirm-flow-cell-sync` command to prevent it from running on every flow cell every time (#2623)

## [51.9.10] - 2023-10-31
### Fixed
- Fix database model error (#2642)

## [51.9.9] - 2023-10-31
### Fixed
- Revert "feat(raredisease): Add raredisease to cg workflow (#2592)" (#2646)

## [51.9.8] - 2023-10-31
### Added
- Cli option: `cg workflow raredisease` (#2592)

## [51.9.7] - 2023-10-30
### Changed
- Use Poetry for packaging and dependency management (#2628)

## [51.9.6] - 2023-10-27
### Changed
- Remove cascade backrefs parameter (#2637)

## [51.9.5] - 2023-10-27
### Fixed
- Fix relationship copy warning (#2614)

## [51.9.4] - 2023-10-27
### Changed
- Ensure connection is closed after CLI commands (#2635)

## [51.9.3] - 2023-10-27
### Fixed
- Fix enums (#2636)

## [51.9.2] - 2023-10-26
### Added
- Add application details to delivery report (#2631)

## [51.9.1] - 2023-10-26
### Fixed
- Fix warnings in tests (#2617)

## [51.9.0] - 2023-10-26
### Added
- Sample_concentration_minimum and sample_concentration_maximum to Application table. (#2629)

## [51.8.1] - 2023-10-25
### Changed
- Removed constant `ARCHIVED_SAMPLE_SHEET` in `cg/constants/housekeeper_tags.py:SequencingFileTag` (#2604)
### Fixed
- Function `get_sample_sheets_from_latest_version` in `cg/apps/housekeeper/hk.py` to remove logic regarding the removed tag (#2604)

## [51.8.0] - 2023-10-24
### Added
- Column "lab_contact_id" to the Customer table. (#2595)

## [51.7.6] - 2023-10-24
### Fixed
- Fixed pipeline version for stored rnafusion analysis (#2625)

## [51.7.5] - 2023-10-24
### Added
- Add pipeline limitations endpoint (#2622)

## [51.7.4] - 2023-10-24
### Changed
- Containerize cg cli (#2610)

## [51.7.3] - 2023-10-23
### Added
- Pipeline specific limitations to delivery report (#2616)

## [51.7.2] - 2023-10-23
### Changed
- Migrate delivery report models to Pydantic v2 (#2579)

## [51.7.1] - 2023-10-23

## [51.7.0] - 2023-10-23
### Added
- New CLI command: cg backup flow-cell (#2586)
- Tests (#2586)
### Changed
- Add general PcdError, DsmcError (#2586)
- Initialize Pdc_api from context (#2586)

## [51.6.14] - 2023-10-20
### Changed
- Upgrade SQLAlchemy to 2.0 (#2615)

## [51.6.13] - 2023-10-19
### Changed
- Toggle future flag on engine (#2611)

## [51.6.12] - 2023-10-19
### Changed
- Reflect changes in housekeeper in the hk module (#2612)

## [51.6.11] - 2023-10-19
### Changed
- Update rnafusion validation cases to avoid compression (#2606)

## [51.6.10] - 2023-10-18
### Fixed
- Fix missed session warning (#2609)

## [51.6.9] - 2023-10-18
### Fixed
- Check if flow cell check is applicable before checking if they are on disk. (#2608)

## [51.6.8] - 2023-10-18
### Fixed
- Fix session merge warnings (#2598)

## [51.6.7] - 2023-10-18
### Fixed
- Patch hk module (#2605)

## [51.6.6] - 2023-10-18
### Fixed
- Now require Pydantic version >= 2.4 (#2602)

## [51.6.5] - 2023-10-18
### Added
- Two more encryption directories (#2588)
- Iteration trough encryption directories when searching for archived flow cells (#2588)
### Fixed
- Test is now a bit better (#2588)

## [51.6.4] - 2023-10-18
### Fixed
- Fix join (#2601)

## [51.6.3] - 2023-10-18
### Fixed
- Fix missed deprecated join syntax (#2600)

## [51.6.2] - 2023-10-17
### Changed
- Extract database module (#2596)

## [51.6.1] - 2023-10-16
### Fixed
- Revert "Extract database initialisation (#2584)(patch)"

## [51.6.0] - 2023-10-16
### Changed
- Split ensure_flow_cell into smaller functions (#2378)
- Implemented the same pre-start-checks for all pipelines (#2378)
### Fixed
- Some tests now test what they are supposed to (#2378)

## [51.5.15] - 2023-10-16
### Changed
- Lock broken sub dependency (#2594)

## [51.5.14] - 2023-10-16
### Added
- Add raredisease to constants (#2590)

## [51.5.13] - 2023-10-16
### Fixed
- Fix deprecated joins (#2589)

## [51.5.12] - 2023-10-16
### Changed
- Extract database initialisation (#2584)

## [51.5.11] - 2023-10-12
### Changed
- Refactor to PEP 0585: https://peps.python.org/pep-0585 (#2587)
### Fixed
- Unused imports (#2587)

## [51.5.10] - 2023-10-11
### Fixed
- Fix deploy instruction in PR template (#2585)

## [51.5.9] - 2023-10-10
### Fixed
- String coercion by default (#2581)
- Default values set. (#2581)

## [51.5.8] - 2023-10-10
### Fixed
- Automatic start of rnafusion by adding read threshold (#2546)

## [51.5.7] - 2023-10-10
### Changed
- Update deprecated model base import (#2578)

## [51.5.6] - 2023-10-10
### Changed
- Upgrade to Python 3.11 (#2568)

## [51.5.5] - 2023-10-09
### Fixed
- String coercion validator to Individuals.father and Individuals.mother. (#2577)

## [51.5.4] - 2023-10-09
### Changed
- Upgrade to Python 3.10 (#2566)

## [51.5.3] - 2023-10-09
### Changed
- Upgrade sqlalchemy to 1.4 (#2499)

## [51.5.2] - 2023-10-09
### Changed
- Upgrade to Python 3.9 (#2565)

## [51.5.1] - 2023-10-09
### Fixed
- If parent is missing, the value is now set to a string instead of an int. (#2570)

## [51.5.0] - 2023-10-09
### Fixed
- Revert "Add lab_contact to Customer (#2560) (minor)" (#2573)

## [51.4.1] - 2023-10-09
### Changed
- Lock genologics package (#2571)

## [51.4.0] - 2023-10-09
### Added
- Column "lab_contact_id" to the Customer table. (#2560)

## [51.3.1] - 2023-10-09
### Changed
- Upgrade core libraries (#2556)

## [51.3.0] - 2023-10-09
### Added
- Encrypt flow cells CLI command (#2526)
- FlowCellEncryptionAPI (#2526)
- Tests (#2526)
- Pigz to Hasta (#2526)
- Slurm configuration for back-up encryption (#2526)
### Changed
- Encryption takes place in `/home/proj/stage/encrypt/` instead of`/home/hiseg.clinical/ENCRYP'T` (#2526)
- Use flow cell id intead od flow cell full name within encrypt dir (#2526)

## [51.2.9] - 2023-10-06
### Changed
- Update deploy instructions (#2563)

## [51.2.8] - 2023-10-05
### Changed
- Primer alias from `UDF/primer` to `UDF/Primer` (#2561)

## [51.2.7] - 2023-10-05
### Changed
- Sort all imports (#2559)

## [51.2.6] - 2023-10-05
### Changed
- Upgrade Python to 3.8 (#2557)

## [51.2.5] - 2023-10-05
### Added
- The constant class `Pipeline` to `cg/constants/constants.py` importing it from cgmodels (#2518)
- The constant class `AnalysisTypes` to `cg/constants/tb.py` importing it from cgmodels (#2518)
### Fixed
- All of the import statements referring to cgmodels now point to the constants in cg (#2518)

## [51.2.4] - 2023-10-05
### Added
- Refactor flow cell SQL filter function (#2527)
- Test (#2527)
### Changed
- Standardize function naming to use ´filter´ instead of get (#2527)
- Sort imports in selected modules (#2527)

## [51.2.3] - 2023-10-04
### Fixed
- Handle database disconnects (#2554)

## [51.2.2] - 2023-10-04
### Changed
- Initial cleanup for refactoring (#2555)

## [51.2.1] - 2023-10-04
### Added
- Tests for the Excel order form validators (#2537)
### Changed
- Validator for numeric_values is stricter (#2537)
- Created constant for the aliases used in ExcelSample. (#2537)

## [51.2.0] - 2023-10-04
### Added
- Cg workflow taxprofiler start-available (#2424)

## [51.1.3] - 2023-10-04
### Added
- Add application limitations table (#2533)

## [51.1.2] - 2023-10-04
### Fixed
- Fix Pydantic deprecation warnings (#2553)

## [51.1.1] - 2023-10-04
### Changed
- Move housekeeper functions into hk api module (#2549)

## [51.1.0] - 2023-10-03
### Changed
- Allowed version for orderform 1508 changed from 28 to 29 (#2552)

## [51.0.9] - 2023-10-03
### Fixed
- Patch sample sheet generation (#2551)

## [51.0.8] - 2023-10-02
### Changed
- Hide logic for retrieving latest sample sheet (#2544)

## [51.0.7] - 2023-10-02
### Added
- Add validators to sample id (#2528)

## [51.0.6] - 2023-10-02
### Fixed
- Fix issues flagged by sonarcloud (#2542)

## [51.0.5] - 2023-10-02
### Changed
- Remove unnecessary wrapper function (#2543)

## [51.0.4] - 2023-10-02
### Fixed
- Fix-overseen-code-smell (#2539)

## [51.0.3] - 2023-10-02
### Changed
- Remove duplicate to_dict method (#2538)

## [51.0.2] - 2023-10-02
### Changed
- Decompressed fastq files now get their tags from the spring file being decompressed. (#2473)

## [51.0.1] - 2023-10-02
### Changed
- Simplify sample sheet parsing (#2525)

## [51.0.0] - 2023-09-29
### Changed
- Feat(clean flow cells) (#2529)

## [50.1.10] - 2023-09-28
### Fixed
- Set reads_updated_at even when a previous value is set. (#2532)

## [50.1.9] - 2023-09-28
### Changed
- Do not exclude cgdragen2 when demultiplexing (#2512)

## [50.1.8] - 2023-09-27
### Fixed
- One FASTQ upload fail no longer blocks other from being uploaded (#2511)

## [50.1.7] - 2023-09-26
### Fixed
- Changed primer alias from UDF/Primer to UDF/primer (#2524)

## [50.1.6] - 2023-09-26
### Changed
- Reuse the tags from one of the fastq files currently being compressed. (#2475)

## [50.1.5] - 2023-09-26
### Changed
- Refactor retrieving sample ids (#2521)

## [50.1.4] - 2023-09-26
### Changed
- Remove dict and legacy entry. Replace with string (#2517)
- Decouple from file system path when querying PDC (#2517)
- Add flow cell specific search pattern (#2517)
- Simplify extracting file path from DCMS output (#2517)

## [50.1.3] - 2023-09-26
### Fixed
- Templates now references sample.reads_updated_at (#2523)

## [50.1.2] - 2023-09-26
### Fixed
- Field validator decorator before class method decorator in remove_missing_files. (#2522)

## [50.1.1] - 2023-09-26
### Fixed
- Fix complicated conditional code smell (#2519)

## [50.1.0] - 2023-09-25
### Added
- Creating sequencing metrics for undetermined non pooled reads (#2494)
- Storing fastq file paths for undetermined non pooled reads (#2494)
- Tests (#2494)

## [50.0.0] - 2023-09-25
### Changed
- Delete(clean flow cells cli) (#2516)

## [49.5.3] - 2023-09-25
### Added
- A test function for `get_cases_to_store ` when called through the MicrosaltAPI (#2505)
### Fixed
- Removed functions `is_qc_required`, `get_completed_cases`, and `get_cases_to_store `. This last one is implemented in the base class with the desired functionality (#2505)
- Remove tests for old `get_cases_to_store` (#2505)

## [49.5.2] - 2023-09-25
### Fixed
- Flow cell view references sequenced_at (#2515)

## [49.5.1] - 2023-09-25
### Changed
- Sample.sequenced_at is now called sample.reads_updated_at. (#2414)

## [49.5.0] - 2023-09-25
### Added
- Field `has_backup` to the `Flowcell` store model (#2510)
- Optional parameter `has_backup` to all the Flowcell-creating functions. (#2510)
- Migration revision file for the changes in the database tables. (#2510)

## [49.4.7] - 2023-09-22
### Fixed
- GisaidSample validation is now done via model_validator instead of field_validator (#2508)
- GisaidAccession validation is now done via model_validator instead of field_validator (#2508)

## [49.4.6] - 2023-09-22
### Fixed
- Post-processing a flow cell now always sets its status to ondisk (#2509)

## [49.4.5] - 2023-09-21
### Changed
- Refactor(clean config) (#2502)

## [49.4.4] - 2023-09-20
### Changed
- Remove alchy from requirements (#2496)

## [49.4.3] - 2023-09-19
### Changed
- Migrate gisaid models (#2410)

## [49.4.2] - 2023-09-19
### Added
- New alembic script with one migration (#2490)
### Fixed
- Removed part of the migration of the old Alembic script (#2490)

## [49.4.1] - 2023-09-19
### Added
- New name of the sequencing step in the NovaSeq X LIMS workflow (#2385)

## [49.4.0] - 2023-09-19
### Added
- Revision (#2462)

## [49.3.0] - 2023-09-19
### Added
- Call to the function `add_tags_if_nonexistent` using the sample id as tag (#2474)
- Included sample id in the list of tags, along with flow cell id and 'fastq'. (#2474)
- Test for the function `store_fastq_path_in_housekeeper` (#2474)
- Fixtures to support the test (#2474)

## [49.2.0] - 2023-09-15
### Added
- Create metrics for non pooled undetermined reads from bclconvert (#2484)

## [49.1.0] - 2023-09-15
### Added
- Create metrics for non pooled undetermined reads from bcl2fastq (#2480)

## [49.0.16] - 2023-09-14
### Fixed
- Patch fluffy sample sheet header (#2483)

## [49.0.15] - 2023-09-14
### Added
- SampleSheetCreator property `is_reverse_complement` instead of making it an internal variable (#2482)
- Tests (#2482)
### Fixed
- The building of index2 in `add_override_cycles` now checks if the sample sheet `is_reverse_complement` to invert order of terms "I" and "N" (#2482)
- `get_hamming_distance_index_2` receives `is_reverse_complement` to take into account for calculation (#2482)

## [49.0.14] - 2023-09-14
### Changed
- Remove index checks (#2477)

## [49.0.13] - 2023-09-14
### Changed
- Replace deprecated Pydantic call (#2479)

## [49.0.12] - 2023-09-14
### Changed
- Update Ruff (#2481)

## [49.0.11] - 2023-09-14
### Added
- Add isort using profile black to pre-commit config and pyproject toml (#2478)

## [49.0.10] - 2023-09-13
### Changed
- Name of fixture `fastq_file_path` to `fluffy_fastq_file_path` (#2476)

## [49.0.9] - 2023-09-13
### Changed
- Find undetermined fastqs for non-pooled samples wip (#2427)

## [49.0.8] - 2023-09-13
### Fixed
- Fix fluffy samplesheet generation and formatting (#2468)

## [49.0.7] - 2023-09-13
### Changed
- Remove missed config field (#2464)

## [49.0.6] - 2023-09-13
### Changed
- Refactor deliverables for rnafusion (#2367)

## [49.0.5] - 2023-09-12
### Added
- A specific fixture (`novaseqx_flow_cell_with_sample_sheet_no_fastq`) for the two tests of the modified function (#2433)
### Changed
- Function `validate_samples_have_fastq_files` in `cg/meta/demultiplex/validation.py` renamed to `validate_flow_cell_has_sample_files` and changed so that all samples must lack a fastq file for it to raise an error (#2433)
- The two tests of the function `validate_flow_cell_has_sample_files`. (#2433)
- The order of the validations in function `is_flow_cell_ready_for_postprocessing`, putting the delivery status first and the sample fastq last. (#2433)
- Removed fixture `bcl_convert_demultiplexed_flow_cell` which was used only by the old tests (#2433)
- Removed fixture `novaseqx_flow_cell_dir_name` and replaced its usage for the already existent flow cell name `novaseq_x_flow_cell_full_name` which is more widely used. (#2433)

## [49.0.4] - 2023-09-12
### Added
- Tests for cases where `total_yield` is 0 (#2469)
### Changed
- `calculate_q30_bases_percentage` and `calculate_average_quality_score` return 0 if `total_yield` is 0 (#2469)

## [49.0.3] - 2023-09-12
### Added
- Functions to calculate the hamming distance independently for index1 (i7) and index2 (i5) according to what we agreed upon on https://github.com/Clinical-Genomics/cg_lims/issues/392 (#2454)
- Tests for the new hamming distance calculators (#2454)
- Functions to update barcode mismatch values for each sample in each SampleSheetCreator class (#2454)
- Functions to calculate override cycles for each sample in each SampleSheetCreator class (#2454)
- Attribute `OverrideCycles` to FlowCellSampleBCLConvert` model (#2454)
### Changed
- Splitted the function `adapt_samples` into `update_indexes_for_samples` and `update_barcode_mismatch_values_for_samples` (#2454)
- Renamed function `adapt_indexes_for_sample` to `pad_and_reverse_complement_sample_indexes` (#2454)
### Fixed
- Removed if statement that excluded NovaSeq6000 barcode mismatches to be updated (#2454)
- Modified the checks for padding to only pass when the samples are from a Bcl2fastq flow cell (#2454)
- Removed repeated fixtures and updated usages (#2454)

## [49.0.2] - 2023-09-12
### Changed
- Change NumberReads validation from > to >= (#2467)

## [49.0.1] - 2023-09-12
### Changed
- Refactor(demux post processing api) (#2463)

## [49.0.0] - 2023-09-12
### Changed
- Delete(cgstats) (#2461)

## [48.0.0] - 2023-09-12
### Changed
- Cleanup of nf options and removal of deprecated ones (#2407)

## [47.0.1] - 2023-09-11
### Changed
- Log-level set to warning for errors thrown by `is_flow_cell_ready_for_postprocessing` (#2457)

## [47.0.0] - 2023-09-11
### Changed
- Delete(TransferFlowcell class) (#2455)

## [46.0.5] - 2023-09-11
### Added
- BeforeValidator coercing the given value to a string if Present, and leaves it as None otherwise. (#2408)

## [46.0.4] - 2023-09-11
### Changed
- We are now looking for any file which path ends with `Stats/Stats.json` (#2432)
### Fixed
- Now correctly raises FileNotFoundError if no file is found (#2432)

## [46.0.3] - 2023-09-11
### Added
- Added an after validator that replaces spaces with underscore for the priority options. (#2441)

## [46.0.2] - 2023-09-11
### Changed
- Remove fixture pytest and name args decorator (#2444)

## [46.0.1] - 2023-09-11
### Changed
- Remove constructor typehints (#2451)

## [46.0.0] - 2023-09-11
### Changed
- Delete(old post processing flow) (#2380)

## [45.5.5] - 2023-09-11
### Added
- Logging when encountering a malformed sample sheet describing expected headers. (#2365)

## [45.5.4] - 2023-09-08
### Fixed
- Extract logic for retrieving sample ids to the `SampleSheet` object (#2445)

## [45.5.3] - 2023-09-08
### Fixed
- Fix overly verbose docstrings (#2437)

## [45.5.2] - 2023-09-08
### Changed
- Migrate sbatch to Pydantic v2 (#2438)

## [45.5.1] - 2023-09-08
### Fixed
- Removed an if statement that excluded NovaSeq6000 to have a header (#2442)

## [45.5.0] - 2023-09-07
### Added
- Method get_samples_to_retrieve in archive.py (#2322)
- Method from_sample_and_destination to instantiate a MiriaObject object (#2322)
- Data class SampleAndHousekeeperDestination (#2322)
- Method retrieve_samples in both ArchiveHandler and in DDNDataflowClient (#2322)
- Method retrieve_samples in SpringArchiveApi (#2322)
- Tests (#2322)
### Changed
- Renamed MiriaFile to MiriaObject (#2322)

## [45.4.5] - 2023-09-07
### Changed
- Refactor bclconvert models (#2423)

## [45.4.4] - 2023-09-07
### Changed
- Refactor bcl2fastq models (#2422)

## [45.4.3] - 2023-09-07
### Changed
- Migrate metrics models (#2421)

## [45.4.2] - 2023-09-07
### Changed
- Migrate demux results (#2428)

## [45.4.1] - 2023-09-06
### Fixed
- Removed call to function blocking finishing of some flow cells (#2429)

## [45.4.0] - 2023-09-06
### Changed
- Change path of demultiplexing output (#2426)

## [45.3.0] - 2023-09-06
### Added
- CLI function to parse the folder in the mounted folder and check if their sync is complete. If so create a CopyComplete.txt file. (#2403)
- `is_syncing_complete` checks if the syncing of a flow cell is complete (#2403)
- `parse_manifest_file` parses the manifest file. (#2403)
- `is_file_relevant` checks if the file is relevant for demultiplexing (#2403)

## [45.2.2] - 2023-09-06
### Added
- Function `validate_samples_have_fastq_files` (#2401)
- Tests for `validate_samples_have_fastq_files` (#2401)
- A try statement that catches the MissingFileError when finishing the flow cell (#2401)
### Changed
- `is_flow_cell_ready_for_postprocessing`, adding a call to `check_if_samples_have_files` (#2401)
- Moved functions from `cg/meta/demultiplex/validation.py` to `cg/meta/demultiplex/utils.py` (#2401)
- `is_valid_sample_fastq_file` (#2401)
- `is_file_path_compressed_fastq ` (#2401)
- `is_lane_in_fastq_file_name ` (#2401)
- `is_sample_id_in_directory_name ` (#2401)
- `is_sample_id_in_file_name` (#2401)
- Moved the tests of the mentioned functions from `tests/meta/demultiplex/test_validation.py` to `tests/meta/demultiplex/test_utils.py` (#2401)
### Fixed
- Changes to docstrings and in-line comments of touched files to compile with the 100-character line rule (#2401)
- Automatic reorganization of imports done by the linter (#2401)

## [45.2.1] - 2023-09-06
### Changed
- Remove unused fixtures (#2425)

## [45.2.0] - 2023-09-05
### Added
- Cg workflow taxprofiler start (#2413)

## [45.1.3] - 2023-09-05
### Changed
- Migrate additional scout models to Pydantic v2 (#2398)

## [45.1.2] - 2023-09-05
### Changed
- Migrate scout tag models to Pydantic v2 (#2411)

## [45.1.1] - 2023-09-04
### Changed
- Migrate archive model to Pydantic v2 (#2409)

## [45.1.0] - 2023-09-04
### Added
- Add tower to cg workflow taxprofiler run (#2357)

## [45.0.17] - 2023-09-04
### Changed
- Migrate mutant models to Pydantic v2 (#2405)

## [45.0.16] - 2023-09-04
### Changed
- Migrate SampleData model to Pydantic v2 (#2390)

## [45.0.15] - 2023-09-04
### Changed
- Migrate sample sheet models to Pydantic v2 (#2394)

## [45.0.14] - 2023-09-04
### Added
- Option to pass delimiter to the csv functions in the io module (#2402)
- Unittest for tsv files (#2402)

## [45.0.13] - 2023-09-04
### Changed
- Migrate slurm model to Pydantic v2 (#2404)

## [45.0.12] - 2023-09-04
### Fixed
- Migrate NIPT models to Pydantic V2 (#2406)
- Add unit tests for NIPT models (#2406)

## [45.0.11] - 2023-09-01
### Fixed
- Fix volume Pydantic field (#2399)

## [45.0.10] - 2023-08-31
### Fixed
- Fix property on Application model (#2397)

## [45.0.9] - 2023-08-31
### Changed
- Basemodels and parsers in apps/orderform (#2358)
- Validators are now outside of the base class and used as annotated validators à la https://docs.pydantic.dev/latest/usage/validators/#annotated-validators. (#2358)

## [45.0.8] - 2023-08-31
### Fixed
- Fix(correct path to novaseqx fastq files) (#2393)

## [45.0.7] - 2023-08-31
### Changed
- Migrate index model (#2392)

## [45.0.6] - 2023-08-30
### Changed
- Refactor sample sheet methods for nf-analysis and update pytests and fixtures (#2360)
### Fixed
- Dry-run logs for config-case for rnafusion (#2360)

## [45.0.5] - 2023-08-30
### Added
- Package for keeping validators for base models. (#2366)
### Fixed
- Pydantic v2 now used in apps/scout. (#2366)

## [45.0.4] - 2023-08-30
### Changed
- Migrate crunchy models (#2376)

## [45.0.3] - 2023-08-30
### Changed
- Remove unused field in model (#2377)

## [45.0.2] - 2023-08-30
### Changed
- Migrate trailblazer pydantic model (#2379)

## [45.0.1] - 2023-08-29
### Added
- Add abort check (#2389)

## [45.0.0] - 2023-08-29
### Changed
- Feat(move to new demux flow) (#2386)

## [44.0.5] - 2023-08-29
### Fixed
- Fix overlooked code smell (#2387)

## [44.0.4] - 2023-08-29
### Fixed
- Fix(fetch HK sample sheet for validation new demux post processing flow) (#2381)

## [44.0.3] - 2023-08-29
### Added
- New check `has_demultiplexing_started_on_deck` (#2382)
- Tests for `has_demultiplexing_started_on_deck` (#2382)
- Tests for `has_demultiplexing_started_locally` (#2382)
### Changed
- New entry point to the CLI after removal of weird import (#2382)
### Fixed
- Fix(rename fastq files in new demux post processing flow) (#2384)

## [44.0.2] - 2023-08-29
### Fixed
- Fix setup.py
- Revert "Fix setup.py"

## [44.0.0] - 2023-08-28
### Added
- Try-except statements that continue if a flow cell failed (#2372)

## [43.1.0] - 2023-08-28
### Fixed
- Fix(bcl converter fetching for demux post postprocessing api) (#2375)

## [43.0.5] - 2023-08-28
### Fixed
- Sequenced_at is set on sample level during `demultiplex finish temporary`. (#2373)

## [43.0.4] - 2023-08-28
### Fixed
- Remove unreachable code (#2374)

## [43.0.3] - 2023-08-25
### Changed
- The referring to the sample sheet in the demux_runs directory to the sample sheet in Housekeeper (#2364)

## [43.0.2] - 2023-08-25
### Changed
- Store and use q30 metrics as percentages (#2352)

## [43.0.1] - 2023-08-25
### Changed
- #2362: Patch new flow cell dir structure (#2363)

## [43.0.0] - 2023-08-24
### Added
- Call to the function `cg/meta/demultiplex/housekeeper_storage_functions.py:add_sample_sheet_path_to_housekeeper` after sample sheet creation, in both `create` and `create-all` commands. (#2343)
- An instance of HousekeeperAPI as parameter of DemultiplexAPI (#2343)
- The function `get_sample_sheet` in DemultiplexAPI that fetches the sample sheet from Housekeeper (#2343)
- The function `sample_sheet_exists_in_hk` in DemultiplexAPI (#2343)
- An additional condition in the DemultiplexAPI function `is_demultiplex_possible` that checks for the sample sheet existence in Housekeeper. (#2343)
### Changed
- Removed functions `copy_sample_sheet` and their tests (#2343)
- Renamed DemultiplexAPI function `unaligned_dir` to `get_slow_cell_unaligned_dir` (#2343)
### Fixed
- Removed parameter `bcl_converter` from CLI function `cg demultiplex samplesheet create-all` (#2343)
- Removed DemuxFlowCell function `demux_sample_sheet_path` as it referred to the copy of the sample sheet that was removed (#2343)
- Added call to the function `add_bundle_and_version_if_non_existent` within the function `add_sample_sheet_path_to_housekeeper`. (#2343)
- Now using the DRY_RUN constant instead of defining the click decorator for dry run for functions `create` and `create-all` (#2343)

## [42.0.0] - 2023-08-24
### Changed
- Refactor(remove cgstats from delete demux api) (#2286)

## [41.0.2] - 2023-08-24
### Changed
- Hermes uses pydantic 2 for its models. (#2351)
- Tests for hermes uses pydantic 2 for its ValidationErrors. (#2351)

## [41.0.1] - 2023-08-23
### Changed
- Cancer somatic SNV uploads (#2297)

## [41.0.0] - 2023-08-23
### Changed
- 2336 copy novaseqx flowcell (#2347)

## [40.12.4] - 2023-08-23
### Fixed
- Fixed the `get_case_by_entry_id` method call to be made to the right object

## [40.12.3] - 2023-08-22
### Changed
- Import pydantic v2 (#2346)
- Set default value for optional. (#2346)

## [40.12.2] - 2023-08-21
### Changed
- Refactor(BackupAPI use flat flow cell structure) (#2344)

## [40.12.1] - 2023-08-21
### Changed
- Refactor token validation (#2313)

## [40.12.0] - 2023-08-21
### Added
- Add(flat flow cell directory structure demux api) (#2349)

## [40.11.1] - 2023-08-21
### Changed
- Update CODEOWNERS (#2353)

## [40.11.0] - 2023-08-17
### Changed
- (feat taxprofiler): Add taxprofiler resolve-compression and run commands (#2106)

## [40.10.1] - 2023-08-17
### Fixed
- Sample validation for NF pipelines and pytests (#2339)

## [40.10.0] - 2023-08-16
### Added
- Add( flat flow cell struct to config) (#2340)

## [40.9.7] - 2023-08-16
### Fixed
- Fix(remove bcl converter option from demultiplex all) (#2338)

## [40.9.6] - 2023-08-15
### Changed
- Refactor(demultiplexing api) (#2329)

## [40.9.5] - 2023-08-15
### Changed
- Feat(dynamic setting of bcl converter) (#2328)

## [40.9.4] - 2023-08-14
### Changed
- Removed get_default_parameters in favour of BaseModel (#2318)

## [40.9.3] - 2023-08-14
### Fixed
- Revert "Migrate app models"

## [40.9.2] - 2023-08-14
### Changed
- Migrate app models

## [40.9.1] - 2023-08-11
### Fixed
- Fix(add samples to flow cell if it already exists) (#2320)

## [40.9.0] - 2023-08-10
### Added
- Method "archive_all_non_archived_spring_files" (#2312)
- A default maximum amount of spring files to archive at once. (#2312)
- Fixture for an authorization token towards Miria. (#2312)
- Test for archive_all_non_archived_spring_files. (#2312)
### Changed
- Renamed archive_folders to archive_files since we are submitting a batch of files. (#2312)

## [40.8.2] - 2023-08-10
### Fixed
- Fix(uncouple statusDB Sample reads from CGstats) (#2294)

## [40.8.1] - 2023-08-10
### Changed
- Removed TowerAnalysisAPI and NextflowAnalysisAPI and replaced by NfBaseHandler NfTowerHandler and NextflowHandler (#2309)

## [40.8.0] - 2023-08-09
### Added
- Fixture for a FileAndSample object. (#2307)
- Fixture for a trimmed local path. (#2307)
### Changed
- Moved class FileAndSample to cg.meta.archive.models (#2307)
- Moved the handler dictionary out of the instantiation of the SpringArchiveAPI (#2307)
- Instead of a DDNDataFlowClient, you give a DataFlowConfig as input to the SpringArchiveAPI. This config is used to instantiate an arbitrary ArchiveHandler. (#2307)
- Renamed "call_corresponding_archiving_method" to "archive_files". (#2307)
- Moved convert_files_into_transfer_data from SpringArchiveAPI to ArchiveHandler. (#2307)
- Added support for creating file transfer data which adapts to whether you are archiving or retrieving files. This is needed as the source and destination given in the request reverses between the two. (#2307)
- Renamed DDNDataFlowConfig to DataFlowConfig, which is intended to be a config which can be used to instantiate the DDN archive handler, but also any other, should we add some in the future. (#2307)
- Archive_folders and retrieve_folders now take a list of files and samples as input, and conversion to the correct format for the handler is done within the ArchiveHandler within this flow. (#2307)
- Renamed sources_and_destinations to miria_file_data within the DDNDataFlowClient. (#2307)
### Fixed
- Some typos and imports. (#2307)

## [40.7.1] - 2023-08-09
### Changed
- Refactor(NfAnalysisAPI) avoid code duplication between rnafusion and taxprofiler (#2308)

## [40.7.0] - 2023-08-08
### Added
- Base class ArchiveModels, specifying what data is necessary to archive a file, as well as which API to use. (#2302)
- Added archive model and dataflow handler to the instantiation of SpringArchiveAPI. (#2302)
- Method call_corresponding_archiving_function, invoking the specified dataflow handler. (#2302)
- Method convert_into_correct_model, converting a file and sample to the format required for the specified flow. (#2302)
- Tests for the two added methods. (#2302)
### Changed
- Renamed ArchiveInterface to ArchiveHandler. (#2302)
- Renamed ArchiveFile to FileTransferData (#2302)

## [40.6.3] - 2023-08-08
### Added
- NfAnalysisAPI class (child of AnalysisAPI) (#2303)
### Changed
- Refactored rnafusion and taxprofile. Common methods have been moved to NfAnalysisAPI from which they inherit (#2303)
- Removed rnafusion- and taxprofile-specific fastq handler (#2303)
- Standard method to name fastq files defined in FastqHandler (#2303)

## [40.6.2] - 2023-08-07
### Added
- Add(samples to flow cell in new demux pp workflow) (#2295)

## [40.6.1] - 2023-08-07
### Fixed
- Fix(decouple nipt upload from cgstats) (#2218)

## [40.6.0] - 2023-08-07
### Added
- Class `FileAndSample` that stores on File and one Sample (#2300)
- Function `add_samples_to_files` which instantiates aforementioned class for each File in a list (#2300)
- Function `get_files_by_archive_location` which returns all FileAndSample in a list which match the given archive_location (#2300)
- Tests for the functions (#2300)

## [40.5.1] - 2023-08-07
### Changed
- Validate sample sheet and handle errors for rnafusion config-case subcommand (#2289)

## [40.5.0] - 2023-08-07
### Added
- Exception handling when calling the archive and retrieve endpoints (#2299)
- Function `create_transfer_request` performing the path curation needed before sending the request (#2299)
- Class `TransferJob` to represent the return of archive and retrieve posts (#2299)
### Changed
- Input to archive_folders & retrieve_folders changed from a dict to a list of already instantiated TransferData objects (#2299)
- Return changed from just the request return, to the actual task_id (#2299)

## [40.4.1] - 2023-08-04
### Added
- Add(force flag to new demux pp flow) (#2288)

## [40.4.0] - 2023-08-04
### Added
- Method to initiate a file model with Sample and File as input (#2298)
- Interface models to inherit from (#2298)
### Changed
- Naming of old models (#2298)

## [40.3.3] - 2023-08-02
### Changed
- Cg now requires a housekeeper version equal or greater than 4.6, but lower than 5.0 (#2296)

## [40.3.2] - 2023-08-01
### Fixed
- Add integration test for post processing of flat flow cell demultiplexed with bclconvert (#2236)

## [40.3.1] - 2023-07-31
### Changed
- Refactor(make hk log less verbose) (#2262)

## [40.3.0] - 2023-07-31
### Added
- `get_files_by_archive_location` which matches sample_ids from housekeeper to samples in statusdb and sort them according to the given archive location (#2282)
- Small functions in `hk.py` to fetch archive information from housekeeper (#2282)
### Changed
- `populated_housekeeper_api` from `MockHousekeeperAPI` to `HousekeeperAPI` (#2282)

## [40.2.3] - 2023-07-28
### Changed
- Refactor(tests in demultiplex post processing) (#2284)

## [40.2.2] - 2023-07-27
### Changed
- Refactor(demux post processing api) (#2275)

## [40.2.1] - 2023-07-26
### Changed
- Added unique suffix for tower names for re-runs (#2283)

## [40.2.0] - 2023-07-25
### Changed
- Removed QC-status constrain from `metrics-deliver`. This subcommand can be performed regardless of the trailblazer status. The logic is now moved to `store`. (#2255)
- `store` and `store-available` accepts now cases with either a QC or COMPLETE as trailblazer status. (#2255)
- `store` checks if metrics_deliverables file exists and runs metrics-deliver if not. This is to avoid cases being stored without performing metrics. (#2255)
- Failed metrics are written with only two decimals in trailblazer comment. (#2255)

## [40.1.5] - 2023-07-25
### Fixed
- Fix validation of sample fastq files ensuring they belong to a specific sample (#2281)

## [40.1.4] - 2023-07-24
### Fixed
- Creation of empty samples bundles in housekeeper in the new flow cell post processing flow (#2276)

## [40.1.3] - 2023-07-24
### Fixed
- Bug adding too many fastq files to a sample bundle in housekeeper (#2280)

## [40.1.2] - 2023-07-21
### Fixed
- Skip flow cell instead of raising exception when it is invalid (#2274)

## [40.1.1] - 2023-07-21
### Fixed
- Improved validation of flow cell before post processing (#2273)

## [40.1.0] - 2023-07-21
### Added
- Except all errors in finish_all_flow_cells_temp (#2271)

## [40.0.1] - 2023-07-20
### Fixed
- Fix( check if sample is present in statusDB before adding a metrics entry) (#2269)

## [40.0.0] - 2023-07-20
### Added
- Add(delete flow cell entries in samplelanemetrics to delete demux api) (#2202)

## [39.1.0] - 2023-07-20
### Added
- Endpoint for retrieving sequencing metrics for a flow cell (#2268)

## [39.0.0] - 2023-07-20
### Added
- Add(temp finish flow cell logic to full command) (#2166)

## [38.3.5] - 2023-07-19
### Fixed
- Sample sheet copy destination in demultiplexed flow cell directory (#2260)

## [38.3.4] - 2023-07-19
### Added
- Crunchy pydantic models previously imported from `cgmodels` to `cg/apps/crunchy/models.py` (#2266)
### Changed
- The version of pydantic in the requirements (#2266)
- All the imports of pydantic so that it uses v1 instead of v2 (#2266)

## [38.3.3] - 2023-07-18
### Added
- Upload forced generated report (#2256)

## [38.3.2] - 2023-07-18
### Changed
- Refactor(remove duplicated attribute) (#2261)

## [38.3.1] - 2023-07-18
### Added
- Add(track demux logs in housekeeper) (#2258)

## [38.3.0] - 2023-07-17
### Changed
- (feat taxprofiler) Add sample_name instead of case_id in the samplesheet (#2231)

## [38.2.10] - 2023-07-17
### Changed
- Feat(copy sample sheet demux post processing new) (#2257)

## [38.2.9] - 2023-07-13
### Changed
- Enhance(set rsync api production QOS to high) (#2254)

## [38.2.8] - 2023-07-13
### Fixed
- Fix(sample column dependence for when parsing sample internal ids from sample sheets) (#2248)

## [38.2.7] - 2023-07-13
### Changed
- Refactor(tests using sql alchemy functions) (#2253)

## [38.2.6] - 2023-07-12
### Changed
- Added threshold (#2252)

## [38.2.5] - 2023-07-12
### Added
- Summary logging of splice junctions upload and of bigwig coverage upload. (#2233)
### Fixed
- Removed an unnecessary check to see whether a case was uploaded, since that check is performed already in an earlier part of the flow. (#2233)

## [38.2.4] - 2023-07-12
### Changed
- Balsamic panel bed name extraction from bed filename (#2222)

## [38.2.3] - 2023-07-11
### Changed
- Refactor transfer of fastq files in new post processing of flow cells (#2237)

## [38.2.2] - 2023-07-11
### Fixed
- Require Pydantic version <2.0 in requirements.txt. (#2245)

## [38.2.1] - 2023-07-11
### Changed
- Feat(add extraction of sample internal ids from sample sheet to sample sheet logic) (#2244)

## [38.2.0] - 2023-07-11
### Added
- Boolean is_clincal to table Customer, and support for setting it. (#2228)

## [38.1.9] - 2023-07-11
### Fixed
- Specified which version to use in the black.yaml to 23.3.0 (or closest one covered by their stability policy). (#2243)

## [38.1.8] - 2023-07-10
### Fixed
- Add integration test for post processing of flow cell demultiplexed with bcl2fastq (#2235)

## [38.1.7] - 2023-07-10
### Changed
- Normal only balsamic analysis starting automatically (#2214)

## [38.1.6] - 2023-07-10
### Changed
- Added novaseqx support flow cell model (#2239)

## [38.1.5] - 2023-07-10
### Added
- Upload of SVs to Scout for UMI cases (#2232)

## [38.1.4] - 2023-07-10
### Added
- Add(novaseqx demux post processing) (#2227)

## [38.1.3] - 2023-07-07
### Fixed
- Add integration test for post processing of bclconvert demultiplexed flow cell (#2224)

## [38.1.2] - 2023-07-07
### Fixed
- Remove direct imports of demux fixtures by moving fixtures into root conftest (#2230)

## [38.1.1] - 2023-07-07
### Fixed
- Remove parsing of unused information from `RunInfo.xml` in sequencing metrics parser (#2229)

## [38.1.0] - 2023-07-06
### Added
- Field to Customer table called "data_archive_location" with type str(32). (#2213)
- Alembic revision to reflect the change. (#2213)

## [38.0.2] - 2023-07-06
### Changed
- The nested dictionary is replaced with a data class containing an rna_sample_id, a dna_sample_name and a list of DNA cases; dna_cases. (#2210)
- Tests reworked to test the new functionality. (#2210)

## [38.0.1] - 2023-07-05
### Changed
- Only store sample fastqs passing q30 in Housekeeper (#2201)

## [38.0.0] - 2023-07-04
### Changed
- Enhance(usability delete flow cell command) (#2204)

## [37.2.0] - 2023-07-04
### Added
- Validation for RNAFUSION orders to only allow one sample per case (#2209)

## [37.1.0] - 2023-07-03
### Added
- Function `cg/apps/demultiplex/sample_sheet/index.py: get_index_pair` (and its test functions). (#2138)
- Function `cg/apps/demultiplex/sample_sheet/index.py: adapt_barcode_mismatch_values_for_sample` (and its test functions) that adapts the barcode mismatch values of a sample. (#2138)
- Functions `get_hamming_distance_index_1` and `get_hamming_distance_index_1` (and its test functions) in `cg/apps/demultiplex/sample_sheet/index.py` that calculate the hamming distance between two indices 1 and 2 respectively. (#2138)
- Function `cg/utils/utils.py:get_hamming_distance` (and its test functions) that calculates the hamming distance between two general strings. (#2138)
- More unit tests for functions in `cg/apps/demultiplex/sample_sheet/index.py` (#2138)
- Function `cg/apps/demultiplex/sample_sheet/create.py:sample_sheet_creator_factory` that defines the type of creator based on the sequencer. (#2138)
- Function `cg/apps/demultiplex/sample_sheet/sample_sheet_creator.py:process_samples_for_sample_sheet` that deals with pre-processing samples before sample sheet generation (#2138)
### Changed
- Removed function `adapt_indexes` in `cg/apps/demultiplex/sample_sheet/index.py` and replaced it with two functions: `adapt_indexes_for_sample` and `adapt_samples`. (#2138)
### Fixed
- Called the function `adapt_samples` over all samples in a lane, not in all the flow cell. Iterate then over lanes. (#2138)

## [37.0.28] - 2023-07-03
### Fixed
- Renamed Illumina Nextera XT Dual to Nextera XT Dual (#2207)

## [37.0.27] - 2023-07-03
### Fixed
- Changed how we find already archived sample sheets, since there were inconsistencies with the tagging. Now we find sample sheets which are tagged with "samplesheet" as well as "archived_sample_sheet". (#2172)

## [37.0.26] - 2023-07-03
### Added
- A return that avoids ùploaded_at` be updated for not uploaded samples (#2203)
### Fixed
- Moved the `self.update_uploaded_at(analysis)` outside the if statement for scout delivery (#2203)

## [37.0.25] - 2023-06-30
### Fixed
- Use q30 threshold when updating the sample read count (#2199)

## [37.0.24] - 2023-06-30
### Fixed
- Fix model import (#2200)

## [37.0.23] - 2023-06-29
### Added
- Add flow cell and sample links to table (#2198)

## [37.0.22] - 2023-06-29
### Fixed
- Change some logging to debug mode (#2196)

## [37.0.21] - 2023-06-29
### Added
- Add STROKE panel to clinical master list (#2188)

## [37.0.20] - 2023-06-29
### Fixed
- Revert "Revert "add(temporary column sample table) (#2192) (patch)" (#2194)" (#2195)

## [37.0.19] - 2023-06-29
### Fixed
- Revert "add(temporary column sample table) (#2192) (patch)" (#2194)

## [37.0.18] - 2023-06-29
### Added
- Add(temporary column sample table) (#2192)

## [37.0.17] - 2023-06-29
### Fixed
- Find sample sheet path in flow cell run directory when transferring housekeeper files in new demultiplex finish (#2191)

## [37.0.16] - 2023-06-29
### Fixed
- Transfer of sequencing data to housekeeper (#2190)

## [37.0.15] - 2023-06-28
### Added
- Add(flow cell exists check) (#2182)

## [37.0.14] - 2023-06-27
### Added
- Relaunch option for rnafusion when using NF-Tower (#2139)

## [37.0.13] - 2023-06-27
### Added
- Check for the demuxcomplete.txt file (#2174)
- Try/except clause when fetching bundes from housekeeper (#2174)

## [37.0.12] - 2023-06-27
### Fixed
- Cascade delete sequencing metrics when flow cell is deleted (#2183)

## [37.0.11] - 2023-06-27
### Fixed
- Fix bug get sample internal ids (#2181)

## [37.0.10] - 2023-06-27
### Changed
- Refactor(functions related to metrics db entry) (#2177)

## [37.0.9] - 2023-06-27
### Changed
- New metagenome ordeform version is now 11 (#2179)

## [37.0.8] - 2023-06-27
### Fixed
- Add constraint for implicit uniqueness rule on sequencing metrics table (#2178)

## [37.0.7] - 2023-06-26
### Fixed
- Retry retrieving the sample sheet from the `Unaligned` directory in the `get_sample_sheet` method (#2176)

## [37.0.6] - 2023-06-26
### Added
- Add creation of delivery.txt (#2159)

## [37.0.5] - 2023-06-26
### Fixed
- Only transfer sample specific fastq-files in the new `cg demultiplexing finish` command (#2165)

## [37.0.4] - 2023-06-26
### Changed
- Allows FASTQ files to not exist when unlinking (#2162)

## [37.0.3] - 2023-06-26
### Changed
- Improve readability of DemuxPostProcessingAPI (#2155)

## [37.0.2] - 2023-06-26
### Added
- Add(delivery-report): support FASTQ_SCOUT data delivery (#2142)

## [37.0.1] - 2023-06-26
### Changed
- Translation delivery report (#2141)

## [37.0.0] - 2023-06-21
### Changed
- Family parameter is now called case. (#2123)
- Updated documentation to reflect this change. (#2123)
- Removed test which was skipped every run. (#2123)
- Changed parameter name case_obj -> case in UploadAPI/upload to match the instantiations. (#2123)

## [36.5.1] - 2023-06-21
### Changed
- Restart flag now works for mip-rna cases with uploaded_at already set. (#2147)
- When uploading an RNA report to a DNA case, a check for uploaded_at being set, is performed. (#2147)

## [36.5.0] - 2023-06-21
### Changed
- `cg demultiplex all` and `cg demultiplex flow-cell` no longer deletes housekeeper files. (#2144)

## [36.4.2] - 2023-06-20
### Fixed
- Rnafusion accreditation is under review. Delivery report should be non-accredited. (#2152)

## [36.4.1] - 2023-06-20
### Fixed
- Cleaning of past directories for rnafusion (#2151)

## [36.4.0] - 2023-06-20
### Added
- Rnafusion as an option in the 1508 OF (#2150)
### Changed
- Latest version of the 1508 OF is now 28 (#2150)
- All fixtures are now of the new version (#2150)

## [36.3.2] - 2023-06-20
### Added
- Add test (#2122)
### Changed
- Remove `get_running_cases` in analysis.py (#2122)

## [36.3.1] - 2023-06-20
### Fixed
- Fix invalid flow cell name (#2148)

## [36.3.0] - 2023-06-19
### Added
- Calculation and update of each samples read count and sequencing date (#2134)

## [36.2.7] - 2023-06-19
### Fixed
- Fix( add filenotfounderror to sequencing metrics parser) (#2143)

## [36.2.6] - 2023-06-19
### Fixed
- Mapped reads percentage calculation in RNAFUSION delivery report. (#2133)

## [36.2.5] - 2023-06-19
### Changed
- Allowed version for the RML orderform is now 16 (#2136)

## [36.2.4] - 2023-06-16
### Changed
- Change python base image to slim-bullseye (#2140)

## [36.2.3] - 2023-06-16
### Changed
- Remove revision for already existing index on sample_internal_id

## [36.2.2] - 2023-06-16
### Added
- Add ruff and pre-commit to requirements-dev-txt (#2129)

## [36.2.1] - 2023-06-15
### Added
- Index on `sample_internal_id` column on the `SampleLaneSequencingMetrics` table. (#2135)

## [36.2.0] - 2023-06-15
### Changed
- Renamed `cg/apps/demultiplex/sample_sheet/novaseq_sample_sheet.py` to `cg/apps/demultiplex/sample_sheet/sample_sheet_creator.py`. (#2121)
- Made the following SampleSheetCreator methods abstract: (#2121)
- `add_dummy_samples` (#2121)
- `get_additional_sections_sample_sheet` (#2121)
- `get_data_section_header_and_columns` (#2121)
- The function `cg/apps/demultiplex/sample_sheet/validate.py:get_raw_samples` to generalise the recognition of headers from any sample sheet (#2121)
- Renamed dummy_sample functions with the prefix `get_` (#2121)
### Fixed
- The fixture `tests/apps/demultiplex/conftest.py:fixture_sample_sheet_bcl2fastq_data_header` to use constants instead of str literals. (#2121)
- The fixture `tests/apps/demultiplex/conftest.py:fixture_valid_sample_sheet_bcl2fastq` to include the previous fixture and avoid DRY. (#2121)
- Renamed sample sheet creator fixtures changing suffix `_object` for `_creator` (#2121)
- Splited the test file `tests/apps/demultiplex/test_sample_sheet.py` into `tests/apps/demultiplex/test_index.py` and `tests/apps/demultiplex/test_dummy_sample.py` (#2121)
- Renamed `tests/apps/demultiplex/test_convert_to_sample_sheet.py` into `tests/apps/demultiplex/test_sample_sheet_creator.py` (#2121)

## [36.1.0] - 2023-06-14
### Added
- Transfer of flow cell data to housekeeper in the new `demultiplex finish flowcell` command (#2119)

## [36.0.4] - 2023-06-14
### Changed
- Remove version limitation on pytest (#2127)

## [36.0.3] - 2023-06-14
### Changed
- Remove docutils from requirements-dev.txt (#2125)

## [36.0.2] - 2023-06-13
### Changed
- Remove snapshottest (#2124)

## [36.0.1] - 2023-06-12
### Added
- Parsing and creation of flow cell in the new `cg demultiplex finish` command (#2115)
### Fixed
- Rename `FlowCell` model to `FlowCellDirectoryData` (#2115)

## [36.0.0] - 2023-06-12
### Added
- FlowCell property `sample_type` which gives the specific FlowCellSample model used in the flowcell (#2117)
- Complete NovaSeqX flow cell output in fixtures (#2117)
- Added the bcl converter and sequencer types in the stdout info when creating and validating sample sheets (#2117)
### Changed
- The CLI command `cg demultiplex samplesheet validate`, adding the parameter `flow-cell-name` as the first positional argument. This is to be able to create a FlowCell object and retrieve the `sample_type`. (#2117)
- The FlowCellSample hierarchy and the names of the models in the following way: (#2117)

## [35.0.2] - 2023-06-08
### Added
- Class SampleSheetNovaSeqXSections (unused for the moment) in `cg/constants/demultiplexing.py` with all the constants needed for constructing the sample sheet content. (#2112)
### Changed
- Moved all the sample sheet NovaSeq6000 related constants to the class SampleSheetNovaSeq6000Sections in `cg/constants/demultiplexing.py`. (#2112)
- Updated usages of old constants for the new ones (#2112)
- Separate the sample sheet content construction in two functions: `get_additional_sections_sample_sheet` which deals with all sections that are not data related, and `get_data_section_header_and_columns` which creates the header and the column names of the data section. These function will differ drastically when the distinction between NovaSeq6000 and NovaSeqX is implemented. (#2112)
### Fixed
- Reorganised `cg/constants/demultiplexing.py` putting classes and constants in alphabetical order (#2112)

## [35.0.1] - 2023-06-08
### Added
- Outline for porting functionality to the new `cg demultixplex finish` command (#2111)

## [35.0.0] - 2023-06-08
### Changed
- Removed parameter "status" from the /cases endpoint. (#2096)

## [34.0.0] - 2023-06-08
### Changed
- Removed all but db_entry and model for Vogue (#2104)

## [33.3.4] - 2023-06-08
### Changed
- Sorted imports, keys and function definition (#2103)
- Standardize filter function names (#2103)

## [33.3.3] - 2023-06-08
### Fixed
- Clean-up after test (#2102)

## [33.3.2] - 2023-06-07
### Fixed
- Replaced a call to the `csv.reader` by `ReadFile.get_content_from_file()` implemented in `cg/io/` in: (#2109)
- `cg/apps/demultiplex/sample_sheet/index.py` (#2109)
- `cg/meta/workflow/fluffy.py` (#2109)

## [33.3.1] - 2023-06-07
### Fixed
- Remove flow cell name and directory as attributes from the DemuxPostProcessingApi (#2108)

## [33.3.0] - 2023-06-07
### Added
- Classes `RunParametersNovaSeq6000` and `RunParametersNovaSeqX` derived from class `RunParameters` with the specification for each file. (#2092)
- The `RunParameterError` type and implemented it in the RunParameters classes (#2092)
- Tests for RunParameter classes (#2092)
### Changed
- Made the class `RunParameters` abstract (#2092)
- The function `is_reverse_complement` in `cg/apps/demultiplex/sample_sheet/index.py` to receive a RunParameters object as parameter and to return False if the sequencer is NovaSeqX. (#2092)
- The function `adapt_indexes` in `cg/apps/demultiplex/sample_sheet/index.py` to receive a RunParameters object as parameter (#2092)
- The instantiation of the run parameters class as it now depends on the flow cell sequencer, in `cg/models/demultiplex/flow_cell.py`. (#2092)
### Fixed
- Run parameters fixtures and fixture files paths (#2092)

## [33.2.3] - 2023-06-07
### Fixed
- Adjust precision for calculated metrics in the `SampleLaneSequencingMetrics` table. (#2101)

## [33.2.2] - 2023-06-07
### Fixed
- Nested list "sample_sheet_content" is now converted to a csv stream before issuing Click.echo in the samplesheet create-all CLI command. (#2105)
- Changed return to continue when using dry run in order to loop through all. (#2105)

## [33.2.1] - 2023-06-02
### Added
- Associate sequencing metrics with flow cell and sample. (#2100)

## [33.2.0] - 2023-06-02
### Added
- Support for placing an order via `api/v1/submit_order/rnafusion` (#2094)
- Support for uploading excel orderforms with rnafusion as data analysis (#2094)

## [33.1.6] - 2023-06-02
### Changed
- Initial commit (#2099)

## [33.1.5] - 2023-06-02
### Changed
- Initialisation of the self.sample_data got changed to include the sample project. (#2090)
- Removed the lims api from a test where the now initialised paramter got added. (#2090)

## [33.1.4] - 2023-06-02
### Changed
- Change read count type on statistics model (#2093)

## [33.1.3] - 2023-06-01
### Changed
- Delivery report (#2089)

## [33.1.2] - 2023-06-01
### Added
- NovaSeqX flow cell directory `tests/fixtures/apps/demultiplexing/flow-cell-runs/nova_seq_x/20230508_LH00188_0003_A22522YLT3/`and `Run Parameters.xml` in it. (#2088)
- NovaSeq600 flow cell directory `tests/fixtures/apps/demultiplexing/flow-cell-runs/nova_seq_6000/` and added the bcl2fastq and dragen flowcell used in tests there. (#2088)
- HiSeq flow cell directory `tests/fixtures/apps/demultiplexing/flow-cell-runs/hiseq/180522_ST-E00198_0301_BHLCKNCCXY/`, replacing it with the one directory up. (#2088)
### Changed
- Removed two fixtures for flow cell ids (`another_flow_cell_id` and `yet_another_flow_cell_id`) and replaced them with either of the existing fixtures `dragen_flow_cell_id` or `bcl2fastq_flow_cell_id`. (#2088)
### Fixed
- Removed unused run parameters file ``. (#2088)
- Removed unused flow cell folder `` (#2088)
- Removed sample sheet files belonging to no flow cell and replaced their usages with sample sheets inside flow cell directories. (#2088)
- Use HiSeq files for HiSeq flow cell, previously it used NovaSeq. (#2088)

## [33.1.1] - 2023-06-01
### Added
- Dummy command for populating the `SampleLaneSequencingMetrics` table. (#2072)

## [33.1.0] - 2023-06-01
### Added
- Add config case (#1998)

## [33.0.6] - 2023-06-01
### Fixed
- Fix(blc convert calculations) (#2087)

## [33.0.5] - 2023-05-31
### Changed
- Parsing metadata (#2079)

## [33.0.4] - 2023-05-30
### Fixed
- Fix broken test due to invalid file path (#2084)

## [33.0.3] - 2023-05-30
### Fixed
- Aggregate `bcl2fastq` demultiplex tile metrics to be per sample and lane (#2083)

## [33.0.2] - 2023-05-30
### Fixed
- Change some fixture scopes to speed up test execution (#2077)

## [33.0.1] - 2023-05-29
### Fixed
- Invalid attribute access on the ` SampleLaneSequencingMetrics` model (#2078)

## [33.0.0] - 2023-05-29
### Changed
- Removed endpoints /families and /families/<family_id> (#2073)

## [32.2.8] - 2023-05-29
### Changed
- Added CSV stream writer to Click.echo statement. (#2070)

## [32.2.7] - 2023-05-29
### Changed
- Feat(xml io controller) (#2074)

## [32.2.6] - 2023-05-29
### Added
- Default values to some attributes of the modified sample models: (#2054)
- Genome version constant to `reference` attribute. (#2054)
- "N" to attribute `control`. (#2054)
- "R1" to attribute `recipe`. (#2054)
- "script" to attribute `operator`. (#2054)
- A function that extracts a sequence within parentheses from a str using regex. (#2054)
- Tests, fixtures and mocks for the aforementioned regex function. (#2054)
### Changed
- Renamed `cg/apps/lims/samplesheet.py` to `cg/apps/lims/sample_sheet.py`. (#2054)
- Renamed models `NovaSeqSample`, `SampleBcl2Fastq`, `SampleDragen` to `FlowcellSample`, `FlowcellSampleBcl2Fastq`, `FlowcellSampleDragen`, respectively, located in `cg/apps/demultiplex/sample_sheet/models.py`. (#2054)
- Removed models `LimsFlowcellSample`, `LimsFlowcellSampleBcl2Fastq` and `LimsFlowcellSampleDragen`. Replaced them with renamed models in `cg/apps/demultiplex/sample_sheet/models.py`. Updated usages. (#2054)
- Renamed attribute `second_index` of class FlowCellSample to `index2`. (#2054)
### Fixed
- Replaced string literals used as `bcl_converter`values for calls to constants in `cg/constants/demultiplexing`. (#2054)
- Replaced the parent class usage with the child class when applicable. (#2054)
- Splitted the "monolithic" function `get_index` in `cg/apps/lims/sample_sheet.py` by evaluating the regex externally. (#2054)
- Changed the regex to avoid failing tests warning about backtracking. (#2054)

## [32.2.5] - 2023-05-27
### Fixed
- Remove most unused functions and classes (#2075)

## [32.2.4] - 2023-05-26
### Changed
- Feat(calculation bcl convert metrics) (#2052)

## [32.2.3] - 2023-05-26
### Fixed
- Population of `SampleLaneSequencingMetrics` from bcl2fastq data. (#2071)

## [32.2.2] - 2023-05-26
### Changed
- Renamed SequencingStatistics model (#2066)
- Removed unnecessary fields from SequencingStatistics model (#2066)
- Renamed fields in SequencingStatistics model (#2066)

## [32.2.1] - 2023-05-26
### Fixed
- Remove all unused imports (#2055)

## [32.2.0] - 2023-05-25
### Fixed
- Force-all will deliver even if not needed (#2061)

## [32.1.0] - 2023-05-25
### Added
- Endpoint /cases/caseid mimicking /families/familyid (#2068)

## [32.0.0] - 2023-05-25
### Changed
- Changed /cases to behave exactly like /families (#2049)

## [31.2.3] - 2023-05-25
### Fixed
- Change name of test helper class (#2059)

## [31.2.2] - 2023-05-25
### Fixed
- Remove unused fixture parameters from tests (#2064)

## [31.2.1] - 2023-05-24
### Fixed
- Removed all unused fixtures (#2053)

## [31.2.0] - 2023-05-23
### Added
- Module for converting parsed bcl2fastq metrics to SequencingStatistics (#2045)
- Module for calculating sequencing metrics (#2045)
- Tests for calculation of metrics (#2045)

## [31.1.6] - 2023-05-23
### Fixed
- Remove `export` cli command (#2048)

## [31.1.5] - 2023-05-23
### Fixed
- Replace deprecated `yield_fixture` with `fixture` (#2050)
- Remove unnecessary test marks (#2050)

## [31.1.4] - 2023-05-23
### Fixed
- Replace deprecated `default` parameter with `dump_default` (#2051)

## [31.1.3] - 2023-05-23
### Fixed
- Remove all status commands (#2047)
- Remove tests for status commands (#2047)
- Remove unused `get_samples` function (#2047)
- Remove unused requirement `ansi` (#2047)

## [31.1.2] - 2023-05-23
### Fixed
- Dict key is now the enum value (#2046)

## [31.1.1] - 2023-05-22
### Changed
- Refactoring of test fixtures to get rid of "_obj" endings. (#2043)
### Fixed
- Slurm_rsync_single_case now uses the customer id tied to the given case. (#2043)

## [31.1.0] - 2023-05-22
### Added
- Function to fetch a sample's RIN value from LIMS (#1990)
- Function to fetch RNA prep input amount of a sample (#1990)
- Necessary LIMS config updates (#1990)

## [31.0.2] - 2023-05-22
### Added
- Tests (#2040)
### Changed
- Refactor and move `verify_case_id_in_statusdb` to `verify_case_exists` from Analysis API to Status DB (#2040)

## [31.0.1] - 2023-05-22
### Changed
- Feat(BCL convert metric parser) (#2028)

## [31.0.0] - 2023-05-22
### Changed
- The CLI of `cg demultiplex samplesheet validate` (#2041)
### Fixed
- Removed attribute `flow_cell_mode` class `cg/apps/demultiplex/sample_sheet/models.py:SampleSheet` (endpoint). (#2041)
- Removed parameter `flow_cell_mode` of functions `validate_sample_sheet` and `get_sample_sheet_from_file` in `cg/apps/demultiplex/sample_sheet/validate.py` and updated its usages and tests. (#2041)
- Removed attribute `self.flow_cell_mode` from class `cg/apps/demultiplex/sample_sheet/novaseq_sample_sheet.py:SampleSheetCreator`. (#2041)
- Removed `click.option` `flow-cell-mode` from CLI command `cg demultiplex samplesheet validate` (`cg/cli/demultiplex/sample_sheet.py:validate_sample_sheet`). (#2041)
- Removed flow cell mode constants in `cg/constants/demultiplexing.py`. (#2041)
- Removed property `mode` in class `cg/models/demultiplex/flow_cell.py:FlowCell`. (#2041)
- Removed property `flow_cell_mode` in class `cg/models/demultiplex/run_parameters.py:RunParameters`. (#2041)
- Removed all tests that tested values of flow cell mode. (#2041)

## [30.3.0] - 2023-05-21
### Added
- Parser for metrics generated by the bcl2fastq demultiplexer software (#2020)

## [30.2.7] - 2023-05-21
### Fixed
- Remove werkzeug lock (#2026)

## [30.2.6] - 2023-05-17
### Changed
- Only the major version of housekeeper is now locked (#2039)

## [30.2.5] - 2023-05-17
### Added
- Constant `S1_mode = "S1"` in `cg/constants/demultiplexing.py`. (#2042)
- The S1 constant in the list of accepted literals for functions `validate_sample_sheet` and `get_sample_sheet_from_file` in `cg/apps/demultiplex/sample_sheet/validate.py` and in property `mode` in `cg/models/demultiplex/flow_cell.py`. (#2042)
- A test function for validation of a S1 sample sheet. (#2042)
- ValidationError to the list of caught executions when creating all sample sheets. (#2042)
### Changed
- The expected type of the attribute `flow_cell_mode` in class `cg/apps/demultiplex/sample_sheet/models.py:SampleSheet`, from `FlowCellMode` to `str`. (#2042)
### Fixed
- The list of accepted flow cell modes in `cg/constants/demultiplexing.py`. (#2042)

## [30.2.4] - 2023-05-16
### Changed
- Feat(read csv into dict in io controller) (#2037)

## [30.2.3] - 2023-05-15
### Changed
- Removed HO, MR, TN from GISAID author list. (#2032)

## [30.2.2] - 2023-05-15
### Changed
- Use io csv with sample sheet (#2019)
- Refactored functions creating and validating sample sheets (#2019)
- All file paths supplied to CSV reader are checked for correct file suffix (#2019)

## [30.2.1] - 2023-05-11
### Added
- `MISEQ` and `NEXTSEQ` constants to the Sequencer types. (#2027)
- Mapping between FlowCellModes and Sequencers (#2027)
- Attribute `mode` to the `FlowCell` class (#2027)
### Changed
- Renamed FlowCellMode `HISEQ_X` to `HISEQX` to be consistent with other constants (#2027)
- Sample sheet validation message (#2027)
### Fixed
- Replaced the new variable `flow_cell.mode` where "S2" or "S4" was hard-wired. (#2027)

## [30.2.0] - 2023-05-11
### Added
- Add taxprofiler case to skip for compression (#2022)

## [30.1.4] - 2023-05-11
### Fixed
- Remove global cache `requests_cache` for the `requests` library (#2023)
- Improve logging for errors when decoding tokens (#2023)

## [30.1.3] - 2023-05-11
### Added
- Entries to the constant class Sequencers in `cg/constants/sequencing.py` to account for NovaSeqX. (#2003)
- Property `sequencer_type` to the FlowCell class that takes values of sequencer names depending on the name of the flow cell. (#2003)
### Changed
- The constructor of SampleSheetCreator class, requiring a FlowCell object as parameter, instead of the FlowCell id and the RunParameters object. Updated all usages as well. (#2003)
- Renamed directories and variables named "flowcell" into "flow_cell" when possible. (#2003)
- Made the explicit distinction between fixtures of flow cell meant to be demultiplexed by bcl2fastq and dragen in the fixtures names. (#2003)
- Gave more explicit names to path fixtures. (#2003)
- Moved fixtures to the general contest to be accessible to tests from different directories. (#2003)
### Fixed
- Removed duplicated fixtures. (#2003)
- Removed RunParameters property `flow_cell_type` which took values "novaseq" or "hiseq" as it was not used anywhere outside tests. In practice, this information can be retrieved from the FlowCell object. (#2003)
- Removed constant class FlowCellType in `cg/constants/demultiplexing.py`. (#2003)

## [30.1.2] - 2023-05-11
### Added
- Caesar delivery for rnafusion (#2018)
### Changed
- Updated upload to include clinical delivery (#2018)

## [30.1.1] - 2023-05-11
### Added
- Adds QC checks into `metrics_deliver`. If QC checks are passed it sets the case as completed. If failed, it sets it as failed and adds a comment with the values of the metrics that failed. (#1997)
### Changed
- Metrics_deliver is included as a first step of the store subcommand (#1997)
- Store-available now selects cases with QC as status in trailblazer instead of `complete` (#1997)

## [30.1.0] - 2023-05-10
### Added
- General `validate_file_suffix` function to IO (#1954)
- Add new `FlowCellMode` constant class (#1954)
### Changed
- Refactored CLI validate_sample_sheet (#1954)
- Add new option to specify --flow-cell-mode to `cg demultiplex samplesheet validate` (#1954)

## [30.0.0] - 2023-05-10
### Fixed
- Upload of RNA cases to scout (#2006)

## [29.8.7] - 2023-05-09
### Fixed
- Invalid import in upload commands (#2017)

## [29.8.6] - 2023-05-09
### Changed
- Start with dry_run (#1993)

## [29.8.5] - 2023-05-09
### Added
- Add structure for parsing of sequencing metrics (#2016)

## [29.8.4] - 2023-05-09
### Fixed
- Remove unnecessary method from cg stats (#2013)

## [29.8.3] - 2023-05-09
### Fixed
- Move models to appropriate model directory (#2012)
- Move find methods to find module (#2012)

## [29.8.2] - 2023-05-08
### Changed
- Use cg.utils.enums instead of cgmodels (#2007)
- Move FLOWCELL_Q30_THRESHOLD enum to cg.constants.sequencing to get rid of dependency in cg.constants.constants. (#2007)

## [29.8.1] - 2023-05-08
### Changed
- Renamed CLI to have clearer names. (#2002)

## [29.8.0] - 2023-05-08
### Added
- Add(sequencing_stats model) (#1996)

## [29.7.1] - 2023-05-05
### Added
- 7 WGS T/N cases to skip compression used for test detection of SVs (#2009)

## [29.7.0] - 2023-05-05
### Added
- Mobile element files to scout load config (#2005)

## [29.6.0] - 2023-05-04
### Added
- Upload of multi-qc-reports related to RNA cases to Scout (#1618)
### Changed
- Upload command for reports to Scout (#1618)

## [29.5.7] - 2023-05-04
### Fixed
- Remove get_project_id and get_sample_id methods (#2001)

## [29.5.6] - 2023-05-04
### Added
- Function `flow_cell_mode` in `cg/models/demultiplex/run_parameters.py` that extracts the flow cell mode (S2/S4) from the run parameters file. (#1995)
- Test functions for the class RunParameters. (#1995)
- Fixture for a run parameters file with different index cycles. (#1995)
- Property `requires_dummy_samples` in RunParameters class that replaces the functionality of `run_type` in a much more clear way. (#1995)
### Changed
- Capitalized the names of path constants in `cg/resources/__init__.py`. (#1995)
- Renamed cycle returning functions with the prefix 'get'. (#1995)
- Renamed `RunParameters.flowcell_type` to `RunParameters.flow_cell_type` (#1995)
- Moved run parameters file fixtures from `tests/apps/demultiplex/conftest.py` to `test/conftest.py` to make them accessible to the model tests. (#1995)
- Moved run parameters test functions from `tests/apps/demultiplex/test_parse_run_parameters.py` to `tests/models/demultiplexing` to be consistent with the location of the functions. (#1995)
- Removed property `run_type` from RunParameters class as it was unclear why it was relating number of index cycles to run type. (#1995)
### Fixed
- The `base_mask` function (also renamed) which had some interchanged values. The function was not used (so no usage was affected by this bug), but it will be useful when building the sample sheet v2. (#1995)

## [29.5.5] - 2023-05-04
### Added
- Jinja2 and urllib3 as dependencies (#1986)
### Changed
- Removed Flask-Alchy, Flask-SQLAlchemy, email-validator and wtforms as dependencies (#1986)

## [29.5.4] - 2023-05-02
### Added
- Adds metrics deliverables for rnafusion. This can be called by cg workflow rnafusion metrics-deliver CASEID. It parses the multiqc-data.json file and creates a metrics_deliverables.yaml file (#1984)

## [29.5.3] - 2023-05-02
### Fixed
- Remove unused sample function from stats api (#1992)

## [29.5.2] - 2023-05-02
### Fixed
- Removed redundant functions from FindHandler (#1989)
- Refactored create_novaseq_flowcell function for better readability and maintainability (#1989)

## [29.5.1] - 2023-05-02
### Added
- Classes for NovaSeqSample, SampleSheet and their dragen and bcl2fastq versions in `cg/apps/demultiplex/sample_sheet/models.py`. (#1983)
- Functions to validate sample sheets in `cg/apps/demultiplex/sample_sheet/validate.py`. (#1983)
- SampleSheetError in `cg/exc.py`. (#1983)
- Sample sheet fixtures in `tests/apps/demultiplex/conftest.py`. (#1983)
- Tests for sample sheet validation functions in `tests/apps/demultiplex/test_validate_sample_sheet.py`. (#1983)
### Changed
- The calls to functions in cgmodels/demultiplex to functions inside cg (#1983)
- Some log statements to formatted strings (#1983)

## [29.5.0] - 2023-04-28
### Added
- Add taxprofiler as an option to cg workflow (#1827)

## [29.4.13] - 2023-04-28
### Changed
- Refactored `get_samples_by_customer_id_list_and_subject_id_and_is_tumour` (#1988)
- Refactored `_add_dna_cases_to_dna_sample` (#1988)

## [29.4.12] - 2023-04-28
### Changed
- Moved exists methods from cgstats models to find handler. (#1985)

## [29.4.11] - 2023-04-28
### Changed
- Query to upload RNA cases matches a list of customer IDs instead of only the same customer ID. (#1782)
### Fixed
- Function `get_samples_by_customer_id_list_and_subject_id_and_is_tumour` did not check tumour state, only tumour=True, it now checks tumour state from the input. (#1782)

## [29.4.10] - 2023-04-28
### Fixed
- Exclude cg-dragen2 from the nodes to be used from the dragen partition (#1987)

## [29.4.9] - 2023-04-27
### Changed
- Normal samples as tumors (#1981)

## [29.4.8] - 2023-04-27
### Added
- Add cram files into deliverables for rnafusion workflow (#1980)
### Changed
- Removed pizzly and squid as deliverables for rnafusion (#1980)

## [29.4.7] - 2023-04-27
### Fixed
- Arriba report upload for rnafusion (#1982)

## [29.4.6] - 2023-04-26
### Added
- Balsamic WES validation cases (#1925)
- RNAfusion validation cases (#1925)

## [29.4.5] - 2023-04-26
### Added
- Teardown method to remove the database session after processing a request (#1973)
### Changed
- Session instantiation now uses the scoped_session helper class (#1973)

## [29.4.4] - 2023-04-25
### Fixed
- Changes default value for FUSIONREPORT_FILTER in the rnafusion workflow. It should be a boolean set to false. (#1974)

## [29.4.3] - 2023-04-24
### Changed
- Default parameters for rnafusion (#1967)

## [29.4.2] - 2023-04-24
### Added
- FindHandler class with methods from the find.py module in cgstats (#1969)
- Find_handler attribute on the StatsApi class (#1969)
### Changed
- Updated all calls to the find functions to go through the StatsApi (#1969)

## [29.4.1] - 2023-04-24
### Added
- Locks revision and compute environment for RNAfusion by using defaults given in the cg config file. (#1960)

## [29.4.0] - 2023-04-24
### Added
- Trusted column to customer table (#1968)
- Pass trusted info in the /options endpoint (#1968)
- Field `skip_reception_control` for incoming samples (#1968)
- Pass `skip_reception_control` to LIMS (#1968)

## [29.3.1] - 2023-04-24
### Fixed
- Temporary patch of broken `to_dict` methods causing endpoints to fail (#1966)

## [29.3.0] - 2023-04-24
### Fixed
- Revert "feat(skip-rc-qc) Add option to skip qc to orders (#1812) (minor)" (#1964)

## [29.2.0] - 2023-04-24
### Added
- Trusted column to customer table (#1812)
- Pass trusted info in the /options endpoint (#1812)
- Field `skip_reception_control` for incoming samples (#1812)
- Pass `skip_reception_control` to LIMS (#1812)

## [29.1.7] - 2023-04-24
### Changed
- Removed all model attributes in the base handler class since they are unnecessary. (#1958)

## [29.1.6] - 2023-04-21
### Fixed
- Patch housekeeper database interactions that were deprecated in the latest release of housekeeper (#1962)

## [29.1.5] - 2023-04-21
### Fixed
- Replace `alchy` with `sqlalchemy` in the housekeeper module (#1956)

## [29.1.4] - 2023-04-21
### Fixed
- Remove unused functions in cg stats. (#1951)

## [29.1.3] - 2023-04-21
### Fixed
- Replace all instances of `from cg.apps.cgstats.db import models as stats_models` with direct model imports wherever possible (#1953)

## [29.1.2] - 2023-04-21
### Fixed
- Calls to handler constructors (#1955)

## [29.1.1] - 2023-04-21
### Fixed
- Cli database initialisation test broken locally (#1952)

## [29.1.0] - 2023-04-20
### Changed
- `add_commit` with `session.add` followed by `session.commit` (#1945)
- `delete_commit` with `session.delete` followed by `session.commit` (#1945)
- `commit` with `session.commit` (#1945)
- `delete` with `session.delete` (#1945)
- `from alchy import Query` with `from sqlalchemy.orm import Query` (#1945)
- `rollback` with `session.rollback` (#1945)
- `close` with `session.close` (#1945)
- `add` with multiple objects with `add_all` (#1945)
- All cg models now inherit from `sqlalchemy.ext.declarative` instead of `alchy.make_declarative` (#1945)
- Each table has its name explicitly specified with the `__tablename__` attribute (#1945)

## [29.0.3] - 2023-04-20
### Added
- Workflow_manager information when adding pending analysis (with slurm as default) (#1940)
- Update date when uploading RNAfusion analysis (#1940)

## [29.0.2] - 2023-04-19
### Changed
- Replaced direct queries on the Family table with existing get_join query methods. (#1949)

## [29.0.1] - 2023-04-19
### Added
- Store Tower ID in a trailblazer config file (#1933)

## [29.0.0] - 2023-04-19
### Changed
- Removed deprecated CLI import functions `cg import_cmd` for Application, Application version (#1931)

## [28.0.5] - 2023-04-19
### Added
- FILTER_BY_ENTRY_ID (#1947)
- Get_application_tag_by_application_version_entry_id(application_version_entry_id: str) -> str (#1947)
### Changed
- Rename FILTER_BY_ENTRY_ID to FILTER_BY_APPLICATION_ENTRY_ID (#1947)

## [28.0.4] - 2023-04-19
### Changed
- Replace sample query filtering with existing sample filters (#1946)

## [28.0.3] - 2023-04-19
### Fixed
- Remove queries from tests (#1948)

## [28.0.2] - 2023-04-18
### Changed
- Deleted the fixture `cg/tests/cli/workflow/rnafusion/conftests:py:fixture_not_existing_case_id` nad replace its usages for `cg/tests/conftest.py:fixture_case_id_does_not_exist`. (#1944)

## [28.0.1] - 2023-04-18
### Fixed
- Fix(get_flow_cells_by_case) (#1938)

## [28.0.0] - 2023-04-18
### Changed
- Name of cli command `cg set family` to `cg set case`. (#1932)
- Name of parameters of these functions from `family_id`to `case_id` (#1932)
- Name of variables that shadowed the names `case` and `cases`. (#1932)
- File name `cg/cli/set/{families.py => cases.py}` (#1932)
- File name `cg/cli/set/{family.py => case.py}` (#1932)
- File name `tests/cli/delete/{test_case.py => test_cli_delete_case.py}` (#1932)
- File name `tests/cli/delete/{test_cases.py => test_cli_delete_cases.py}` (#1932)
- File name `tests/cli/set/{test_family.py => test_cli_set_case.py}` (#1932)
- File name `tests/cli/set/{test_families.py => test_cli_set_cases.py}` (#1932)
- File name `tests/cli/set/{test_flowcell.py => test_cli_set_flowcell.py}` (#1932)
- File name `tests/cli/set/{test_list_keys.py => test_cli_set_list_keys.py}` (#1932)
- File name `tests/cli/set/{test_sample.py => test_cli_set_sample.py}` (#1932)
- File name `tests/cli/set/{test_samples.py => test_cli_set_samples.py}` (#1932)

## [27.3.13] - 2023-04-18
### Fixed
- Fix(get_flow_cells_by_statuses) (#1935)

## [27.3.12] - 2023-04-18
### Added
- Customer filter EXCLUDE_INTERNAL_ID (#1941)
### Changed
- Use Customer and Sample filters in _get_filtered_case_query (#1941)
### Fixed
- Move _get_filtered_case_query to base handler (#1941)

## [27.3.11] - 2023-04-18
### Changed
- Rename `get_flow_cell(self, flow_cell_id: str) -> Flowcell` to `get_flow_cell_by_name(self, flow_cell_name: str) -> Flowcell` (#1942)
- Rename GET_BY_NAME_PATTERN to GET_BY_NAME_SEARCH (#1942)
- Rename GET_BY_ID to GET_BY_NAME (#1942)
### Fixed
- Use flow cell filter functions (#1942)

## [27.3.10] - 2023-04-18
### Fixed
- Remove unnecessary revisions (#1943)

## [27.3.9] - 2023-04-17
### Changed
- Refactor function names (#1939)

## [27.3.8] - 2023-04-17
### Added
- Revisions for deleting unused Backup and Backuptape models (#1937)
### Changed
- Removed unused Backup and Backuptape models (#1937)

## [27.3.7] - 2023-04-17
### Changed
- Remove unused function (#1927)

## [27.3.6] - 2023-04-17
### Fixed
- Revert "initial commit"

## [27.3.5] - 2023-04-17
### Changed
- Initial commit

## [27.3.4] - 2023-04-17
### Changed
- Use case filter functions (#1921)

## [27.3.3] - 2023-04-17
### Fixed
- The name of the parameter `panels` to `panel_abbreviations` when calling the cli command `family`. (#1929)

## [27.3.2] - 2023-04-17
### Fixed
- Fix(flow_cells api call) (#1923)

## [27.3.1] - 2023-04-17
### Changed
- Refactor(get_samples_by_any_id) (#1911)

## [27.3.0] - 2023-04-17
### Added
- Added option to give a specific reference directory via the CLI to `config-case` and `start` (#1861)

## [27.2.15] - 2023-04-17
### Changed
- Add default for min seq depth in applications (#1904)
### Fixed
- Fix #1728 (#1904)

## [27.2.14] - 2023-04-15
### Added
- ```python (#1924)
### Changed
- Replaced call to cases() with get_not_analysed_cases_by_sample_internal_id() (#1924)

## [27.2.13] - 2023-04-14
### Added
- Get_cases_in_past_days(days: int) -> List[Family] (#1922)
- GET_NEW filter (#1922)
### Changed
- Replaced call to cases with get_cases_in_past_days(days=31) (#1922)
- Rename GET_OLD to GET_NEW (#1922)

## [27.2.12] - 2023-04-14
### Fixed
- Remove unused functions (#1920)

## [27.2.11] - 2023-04-13
### Added
- Caching of Google OAuth certificate (#1916)

## [27.2.10] - 2023-04-13
### Fixed
- Improved caching of installed Python packages in workflow actions (#1917)

## [27.2.9] - 2023-04-13
### Changed
- Remove unused analyses get function (#1915)

## [27.2.8] - 2023-04-12
### Changed
- Removed method (#1909)

## [27.2.7] - 2023-04-12
### Fixed
- Cleaned up ddn api according to comments (#1912)

## [27.2.6] - 2023-04-12
### Changed
- Feat(CSV reader module) (#1910)

## [27.2.5] - 2023-04-12
### Changed
- Dispatcher-update (#1897)

## [27.2.4] - 2023-04-11
### Changed
- Use filtering function when deleting flow cell (#1902)
- Use flow cell id instead of name in function call (#1902)

## [27.2.3] - 2023-04-11
### Changed
- Refactor(analyses-to-deliver) (#1898)

## [27.2.2] - 2023-04-11
### Changed
- Refactor latest anelyses (#1900)

## [27.2.1] - 2023-04-11
### Added
- Unit tests for case-sample filter functions in `tests/store/filters/test_status_case_sample_filters.py`. (#1903)
- The distinction between entry id and internal id in the name of the filter functions in `tests/store/filters/test_status_case_sample_filters.py` (#1903)
- Fixture for `invalid_sample_id`in `tests/conftest.py`. (#1903)
- Tests for `get_case_samples_by_case_id` and `get_case_sample_link`. (#1903)
### Changed
- The name of the function `family_sample` in `cg/store/find_busines_data.py` to `get_case_samples_by_case_id` and its parameters. (#1903)
- Tests for `get_case_samples_by_case_id`. (#1903)
- The location of the store_with_analyses_for_cases fixture, moved one level up (from `tests/store/api/conftest.py` to `tests/store/conftest.py`. (#1903)
- The name of the function `get_cases_from_sample` in `cg/store/find_busines_data.py` to `get_cases_from_sample_entry_id`. (#1903)
- The name of the function `link` in `cg/store/find_busines_data.py` to `get_case_sample_link`. (#1903)

## [27.2.0] - 2023-04-11
### Added
- Function to archive folders (#1733)
- Function to retrieve folders. (#1733)
- Tests for functions constructing the dict payload (#1733)

## [27.1.64] - 2023-04-05
### Added
- Function `get_application_version_by_application_id` in `cg/store/api/find_basic_data.py`. (#1885)
- Tests for `get_current_application_version_by_tag`. (#1885)
- File `tests/store/api/find/test_find_basic_data_application_version.py` with all tests for application version functions. (#1885)
- Fixture for invalid application tag and pieces dictionary (#1885)
- Function `add_application_version` in `tests/store_helpers.py` (#1885)
- Tests for function `add_application_version`. (#1885)
### Changed
- Name of function `current_application_version` in `cg/store/api/find_basic_data.py` to `get_current_application_version_by_tag`. (#1885)
- Name of function `add_version` in `cg/store/api/add.py` to `add_application_version`. (#1885)
- Used base store when possible and left custom store fixtures for special cases. (#1885)
- The name of the attribute `application_id` to `application_entry_id` when applicable. (#1885)

## [27.1.63] - 2023-04-04
### Fixed
- Revert "refactor(latest_analyses) (#1865)" (#1899)

## [27.1.62] - 2023-04-04
### Added
- Filter function `filter_analyses_by_started_at` (#1865)
- Test for filter function (#1865)
- Test for `get_analyses_by_case_entry_id_and_latest_started_at_date` (#1865)
### Changed
- Function name `latest_analyses` renamed to `get_analyses_by_case_entry_id_and_latest_started_at_date` (#1865)

## [27.1.61] - 2023-04-04
### Changed
- Use cache in actions (#1891)

## [27.1.60] - 2023-04-04
### Fixed
- MIP upload of index files, reverting latest file extraction for VCFs (#1895)

## [27.1.59] - 2023-04-04
### Changed
- Refactor(get_analyses_before) (#1888)

## [27.1.58] - 2023-04-03
### Changed
- Docstring fix (#1896)

## [27.1.57] - 2023-04-03
### Changed
- Bugfix(existing sample search) (#1894)

## [27.1.56] - 2023-04-03
### Changed
- Bugfix(searching exisitng sample) (#1893)

## [27.1.55] - 2023-04-03
### Fixed
- Including full paths of FASTQ and SPRING files in HK (#1856)

## [27.1.54] - 2023-04-03
### Changed
- BugFix(dispatch ignore self) (#1892)

## [27.1.53] - 2023-04-03
### Changed
- Function dispatcher module (#1890)

## [27.1.52] - 2023-04-03
### Fixed
- Fix(cg/meta/backup.py Nonetype.to_archive bug) (#1884)

## [27.1.51] - 2023-04-03
### Changed
- Delivery report template uploaded to Scout files section (#1868)
### Fixed
- Extraction of the latest file from HK for delivery reports and Scout uploads (#1868)

## [27.1.50] - 2023-03-31
### Changed
- Use store instead of base_store wherever possible
- Refactor families filter function (#1860)
### Fixed
- Revert "Use store instead of base_store wherever possible"

## [27.1.49] - 2023-03-30
### Fixed
- Renamed `get_customer_by_customer_id` to `get_customer_by_internal_id` (#1871)
- Renamed parameter `customer_id` to `customer_internal_id` (#1871)
- Renamed internal customer name enum (#1871)

## [27.1.48] - 2023-03-30
### Fixed
- Remove unused parameter threshold in ScoutApi upload (#1872)

## [27.1.47] - 2023-03-30
### Fixed
- Remove dead get_project_name function (#1874)

## [27.1.46] - 2023-03-30
### Fixed
- Remove dead function get_sequenced_date (#1875)

## [27.1.45] - 2023-03-30
### Fixed
- Remove dead functions from the lims api (#1876)

## [27.1.44] - 2023-03-30
### Fixed
- Remove unused function `is_demultiplexing_ongoing` (#1878)

## [27.1.43] - 2023-03-30
### Fixed
- Remove unused `get_nlinks` function. (#1881)

## [27.1.42] - 2023-03-30
### Fixed
- Remove commented out code (#1882)

## [27.1.41] - 2023-03-30
### Fixed
- Remove all unused exceptions (#1883)

## [27.1.40] - 2023-03-29
### Changed
- Refactor(move queries to findhandler) (#1867)

## [27.1.39] - 2023-03-28
### Fixed
- Remove dead functions `family_has_correct_number_tumor_normal_samples` and `get_valid_cases_to_analyze`. (#1847)

## [27.1.38] - 2023-03-28
### Changed
- Refactor(function analysis) (#1864)

## [27.1.37] - 2023-03-28
### Added
- Filter query functions for Application Version (#1826)
- Test functions for the filter functions (#1826)
- Store fixtures for the test functions (#1826)
### Changed
- Reorganized functions and tests so that they are in alphabetical order of their respective model (#1826)

## [27.1.36] - 2023-03-28
### Fixed
- Refactor filtering for retrieving running cases (#1853)

## [27.1.35] - 2023-03-28
### Changed
- Refactor(remove analyses function) (#1846)

## [27.1.34] - 2023-03-28
### Fixed
- Extract filtering of cases on ticket (#1854)

## [27.1.33] - 2023-03-28
### Fixed
- Extract filters for Family by customer entry id and case name (#1858)

## [27.1.32] - 2023-03-28
### Fixed
- Remove unused function cases_to_store (#1859)

## [27.1.31] - 2023-03-28
### Changed
- Refactor(get_samples_by_subject_id) (#1845)

## [27.1.30] - 2023-03-28
### Changed
- Refactor(add analysis filters and tests) (#1849)

## [27.1.29] - 2023-03-27
### Added
- Add new function to get samples by list of customer IDs (#1852)

## [27.1.28] - 2023-03-27
### Changed
- Refactor(find_samples) (#1844)

## [27.1.27] - 2023-03-27
### Changed
- Added new balsamic validation case | patch

## [27.1.26] - 2023-03-27
### Fixed
- Refactor filtering of cases by entry id (#1840)

## [27.1.25] - 2023-03-24
### Added
- New functions and tests for them: (#1843)
- `get_pools_to_invoice_query` (#1843)
- `get_samples_to_invoice_query` (#1843)
- `get_customers_to_invoice` (#1843)
- New tests for: (#1843)
- `get_samples_to_invoice_for_customer` (#1843)
- `get_pools_to_invoice_for_customer` (#1843)
### Changed
- `get_samples_to_invoice` to `get_samples_to_invoice_for_customer` (#1843)
- `get_pools_to_invoice` to `get_pools_to_invoice_for_customer` (#1843)
### Fixed
- Functionality adapted to new function format (#1843)

## [27.1.24] - 2023-03-24
### Changed
- Initial commit (#1848)

## [27.1.23] - 2023-03-24
### Changed
- Refactor(get by enquiry sample function) (#1841)

## [27.1.22] - 2023-03-24
### Changed
- Replaced family function with get_case_by_internal_id (#1837)
### Fixed
- Refactored filtering on internal id for cases (#1837)

## [27.1.21] - 2023-03-23
### Changed
- Refactor(function active_sample) (#1838)

## [27.1.20] - 2023-03-23
### Fixed
- Fix(trailblazer can't fetch cases) (#1839)

## [27.1.19] - 2023-03-23
### Changed
- Refactor(sample add filters and tests) (#1835)
- Refactor(move files add and collect tests sample) (#1836)

## [27.1.18] - 2023-03-23
### Changed
- Refactor(get_all_samples function names) (#1834)

## [27.1.17] - 2023-03-23
### Changed
- Refactor(serrver/api variables) (#1833)

## [27.1.16] - 2023-03-22
### Fixed
- Typo in cleanup for failed flow cells (#1829)

## [27.1.15] - 2023-03-22
### Changed
- Updated housekeeper to version 4.0.0 (#1824)
### Fixed
- Patched breaking changes in housekeeper 4.0.0 (#1824)

## [27.1.14] - 2023-03-21
### Changed
- The location and name of the test filter scripts for customer, organism, panel and user. (#1828)

## [27.1.13] - 2023-03-21
### Fixed
- Replaced undefined function (#1825)

## [27.1.12] - 2023-03-21
### Fixed
- Remove unused imports (#1821)

## [27.1.11] - 2023-03-21
### Changed
- RNAfusion head job runs in as a slurm job instead of in the background (#1814)

## [27.1.10] - 2023-03-21
### Changed
- Refactor(server/api.py function names) (#1815)

## [27.1.9] - 2023-03-21
### Fixed
- Lock housekeeper version to the latest minor version. (#1823)

## [27.1.8] - 2023-03-21
### Changed
- RNAfusion launch directory is set as case directory (#1818)

## [27.1.7] - 2023-03-20
### Fixed
- Add Panel filters (#1792)

## [27.1.6] - 2023-03-20
### Changed
- Refactor set case command (#1793)

## [27.1.5] - 2023-03-20
### Fixed
- Add error handling and logging for retrieving case files from version (#1809)

## [27.1.4] - 2023-03-20
### Changed
- Location and names of filter scripts for Organism and User -> moved to `store/api/filters` (#1813)

## [27.1.3] - 2023-03-17
### Added
- Tests for invoice model (#1810)
- Minor refactoring of `get_invoice_by_id` to `get_invoice_by_entry_id` (#1810)

## [27.1.2] - 2023-03-17
### Added
- Tests for pool filters (#1800)
- Tests for pool filter callers (#1800)
- Pool filters (#1800)
- Pool filter callers (#1800)
### Changed
- Refactored bigger functions into functions that have one purpose (#1800)

## [27.1.1] - 2023-03-16
### Added
- Counter variable `number_previously_linked_files`. (#1803)
### Changed
- The error type when no files are found to `MissingFilesError`. (#1803)
- The name of the counter `number_linked_files` to `number_linked_files_now`. (#1803)
- When the file already exists, increase the counter `number_previously_linked_files` by one after warning the user. (#1803)
- The guard checks if both `number_previously_linked_files`. and `number_linked_files_now` is zero. (#1803)

## [27.1.0] - 2023-03-16
### Added
- Tower support for RNAfusion which now is used by default. Nextflow can still be used with the --use-nextflow option (#1797)
- Add revision and compute-env as CLI options (#1797)
### Changed
- Unify RNAfusion CLI options to "--" syntax (#1797)
- Included slurm qos and account in params-file (#1797)

## [27.0.11] - 2023-03-16
### Fixed
- Fix store model imports (#1804)

## [27.0.10] - 2023-03-16
### Changed
- The reference to the function `store.tag` now points to `store.get_tag`. (#1806)

## [27.0.9] - 2023-03-16
### Added
- Tests for Application model functions (#1798)
### Changed
- Function naming (#1798)
- Refactored statusDB access to go via filter functions (#1798)
- Refactored applications() into multiple functions (#1798)
- Refactored applications() calls into new function calls of smaller functions (#1798)
### Fixed
- MockApplication to be iterable to conform to new List[Application] return type of get_applications() function (#1798)

## [27.0.8] - 2023-03-15
### Fixed
- Replace usage of old function _get_pool_query() (#1805)
- Replace usage of old function _get_sample_query() (#1805)

## [27.0.7] - 2023-03-15
### Added
- A `_get_query` function to get queries for just one table. (#1784)
### Changed
- BaseHandler is now a real dataclass (#1784)
- Moved several queries into BaseHandler (#1784)

## [27.0.6] - 2023-03-15
### Added
- Add file tags to protect in Housekeeper for Balsamic analysis (#1769)

## [27.0.5] - 2023-03-14
### Added
- An extra check in `ensure_flow_cells_on_disk` to avoid aborting with downsampled cases (#1791)
- An extra check in `ensure_flow_cells_on_disk` to avoid aborting with external cases (#1791)

## [27.0.4] - 2023-03-14
### Changed
- Refactor organism filters (#1790)

## [27.0.3] - 2023-03-14
### Changed
- Refactor user filters (#1789)

## [27.0.2] - 2023-03-13
### Added
- Filter queries for cg.store.models Application, Pool, Sample, Invoice (#1767)
- Refactored SQL queries (#1767)
- Added test for filters (#1767)
- Added tests for filter callers (#1767)

## [27.0.1] - 2023-03-13
### Fixed
- Creation of the config using balsamic-umi (#1796)

## [27.0.0] - 2023-03-13
### Added
- Tests (#1780)
### Changed
- Refactor customer SQL query and filter (#1780)
- `cg add family` to `cg add case` (#1780)
- `cg add customer` option `--collaboration` to `collaboration_internal_ids` (#1780)
- `cg add sample` option `application` to `application-tag`, `--downsampled` to `--down_sampled` (#1780)
- `cg add relationship` option: `mother` to `mother-id`, `father` to `father-id`, `family_id` to `case-id` (#1780)
- `cg get family` to `cg get case` and option `family_ids` to `case-ids`, `--customer` to `--customer-id` (#1780)
- `cg get sample` option `--families/--no-families` to `--cases/--no-cases`, `sample_ids` to `sample-ids`, --hide-flowcell` to `--hide-flow-cell`, (#1780)
- `cg get analysis` option `case_id` to `case-id` (#1780)
- `cg get relationship` option `family_id` to `case-id` (#1780)
- `cg get flowcell` to `cg get flow-cell`and option `flowcell_id` to `flow-cell-id` (#1780)
### Fixed
- Bug in `cg add customer` where `--collaboration` was treated as a string option, but should have been a list. (#1780)

## [26.7.5] - 2023-03-13
### Added
- Add missing module (#1795)

## [26.7.4] - 2023-03-13
### Fixed
- Move filters into separate directory (#1787)

## [26.7.3] - 2023-03-13
### Fixed
- Standalone use of creating scout load config for BALSAMIC analyses (#1788)

## [26.7.2] - 2023-03-07
### Fixed
- Revert CORS origin restriction (#1779)

## [26.7.1] - 2023-03-07
### Fixed
- Fix #1689 - add DSD-S to DSD combo (#1764)

## [26.7.0] - 2023-03-07
### Added
- Tests for new collaboration functions (#1778)
### Changed
- Moved collaboration function into higher order apply function (#1778)

## [26.6.3] - 2023-03-03
### Fixed
- Use Pedigree value as key instead of object for MIP-config (#1781)

## [26.6.2] - 2023-03-03
### Changed
- Refactor inconsistent paramater usage (#1776)

## [26.6.1] - 2023-03-02
### Added
- Evaluation of exit status of function `upload_rna_to_scout`, which raises a `RuntimeError` if exit status == 1, continue with normal execution if exit status == 0. (#1773)

## [26.6.0] - 2023-03-02
### Fixed
- Fix query bug (#1775)

## [26.5.1] - 2023-03-02
### Added
- Tests (#1770)
### Changed
- Bed version SQL queries and filters (#1770)

## [26.5.0] - 2023-03-02
### Added
- Force flag to sample sheet creation which then skips the validation (#1774)

## [26.4.3] - 2023-03-02
### Added
- Evaluation of `number_linked_files == 0` and raising of DeliveryReportError if that is the case. (#1765)
- Fixtures for father and mother samples and fixtures for the list of samples of the whole family. (#1765)
- Fixtures for the path to cram files for the father and mother samples and the fixture for the list of their paths. (#1765)
### Changed
- The name of 'sample-tag' for 'cram' for the tests. (#1765)

## [26.4.2] - 2023-03-02
### Changed
- Only accept requests from specific origins (#1687)

## [26.4.1] - 2023-03-01
### Added
- RNAfusion CLI options: -config for nextflow specific configurations and -params-file for pipeline specific options (#1768)
- Default params-file is created when config_case for RNAfusion (#1768)
### Changed
- Removed pipeline specific options in favour of params-file (#1768)

## [26.4.0] - 2023-03-01
### Changed
- Iterate trough analysed samples instead of all samples in a case (#1741)

## [26.3.5] - 2023-02-28
### Added
- Tests (#1766)
### Changed
- Refactor bed sql queries and filters (#1766)

## [26.3.4] - 2023-02-27
### Fixed
- Delete copied data and reports after delivery to FOHM (#1763)

## [26.3.3] - 2023-02-27
### Added
- Tests (#1747)
### Changed
- Removed flow cells function and replaced it with unit tested, decoupled pure functions (#1747)
- Renamed CLI cmd `ensure-flowcells-ondisk` to `ensure-flow-cells-on-disk` (#1747)

## [26.3.2] - 2023-02-27
### Fixed
- Filter SQL functions (#1754)

## [26.3.1] - 2023-02-24
### Fixed
- Fix(Nipt orders get wrong priority) (#1746)

## [26.3.0] - 2023-02-23
### Added
- Cleanup commands for each balsamic pipeline. (#1761)

## [26.2.1] - 2023-02-22
### Fixed
- MIP RNA upload (#1760)

## [26.2.0] - 2023-02-21
### Added
- Scout support for RNAfusion (#1693)

## [26.1.2] - 2023-02-21
### Changed
- The clean commands no long checks if cases exists and has samples before cleaning (#1757)

## [26.1.1] - 2023-02-21
### Fixed
- Fix #1752 - PanelApp Green in masterlist (#1753)

## [26.1.0] - 2023-02-20
### Added
- MipUploadAPI class which serves as parent class for the DNA and RNA upload classes. The upload function is in the parent class. (#1742)
- MipRNAUploadAPI. child of MipUploadAPI (#1742)
- MipDNAUploadAPI child of MipUploadAPI (#1742)
- In `cg/cli/upload/base.py`, the conditional that tests if the analysis pipeline is MipRNA to initialize the correct uploader. (#1742)
### Changed
- The folder structure in `cg/meta/upload` where the mip `.py`files where the three classes are defined are in a new folder called `mip`. (#1742)
- The prefix of pytest fixtures from `rna-mip` and `dna-mip` to `mip-dna` and `mip-rna`, respectively, to integrate better with the ` cli `and `meta` commands (#1742)

## [26.0.9] - 2023-02-17
### Fixed
- Update deprecated actions (#1750)
- Replace deprecated commands (#1750)

## [26.0.8] - 2023-02-15
### Changed
- Gens (#1706)

## [26.0.7] - 2023-02-14
### Fixed
- Replace copy of entire build context in Dockerfile (#1744)

## [26.0.6] - 2023-02-14
### Added
- Tests for some selected date functions (#1738)
- Refactored utils.py code (#1738)

## [26.0.5] - 2023-02-14
### Changed
- Locked openpyxl to release 3.0.10 (#1743)

## [26.0.4] - 2023-02-13
### Added
- Add csrf protection (#1737)

## [26.0.3] - 2023-02-13
### Added
- The function `mip_rna_past_run_dirs` in `/cg/cli/workflow/commands.py` to clean old MIP RNA cases (#1734)
- The test function `test_cli_workflow_clean_mip_rna` (#1734)
### Changed
- Renamed the function `mip_past_run_dirs` in `/cg/cli/workflow/commands.py` to `mip_dna_past_run_dirs` as it was only cleaning MIP DNA cases (#1734)
- Renamed the test function `test_cli_workflow_clean_mip` to `test_cli_workflow_clean_mip_dna` (#1734)
- Added `mip_dna_past_run_dirs` and `mip_rna_past_run_dirs` to the `click.group` in `cg/cli/clean.py` and removed `mip_past_run_dirs` (#1734)
### Fixed
- Removed a forgotten TODO comment in MIP (#1734)

## [26.0.2] - 2023-02-13
### Changed
- Enable demux on dragen2 (#1726)

## [26.0.1] - 2023-02-06
### Changed
- Balsamic analysis taking normal samples as input. (#1717)
- Delivery report minor formatting. (#1717)

## [26.0.0] - 2023-02-06
### Added
- New CLI command to clean old demultiplexed-runs folders (#1718)
### Changed
- Reactor "clean" code (#1718)

## [25.3.0] - 2023-02-01
### Added
- A flag --ignore-missing-bundles f the deliver ticket and deliver analysis command. (#1722)

## [25.2.2] - 2023-02-01
### Changed
- Adjust samplesheet parsing fluffy (#1705)

## [25.2.1] - 2023-02-01
### Changed
- New linting (#1725)

## [25.2.0] - 2023-02-01
### Added
- Action for cancelling samples in status-db (#1704)

## [25.1.0] - 2023-01-25
### Changed
- Adding mitodel to scout (#1714)

## [25.0.0] - 2023-01-25
### Added
- Add new store demultplexed-flow-cell command to include sequencing file on flow cell and/or sample bundle. Also update SPRING metadata file with the included paths. (#1680)
- Add tests (#1680)
### Changed
- Changed store flowcell argument too flow-cell (#1680)

## [24.1.1] - 2023-01-25
### Fixed
- Raise min memory for Crunchy process (#1713)

## [24.1.0] - 2023-01-24
### Added
- QC check before store-available is run (#1655)
- QC command in `cg workflow microsalt` to perform a QC on a micorsalt case (#1655)

## [24.0.9] - 2023-01-23
### Added
- A check to be done before responding to any request, where it is declined if it is not a HTTPS request (#1682)

## [24.0.8] - 2023-01-23
### Added
- Integrity hash to all 11 external scripts used in the invoices app (#1692)

## [24.0.7] - 2023-01-20
### Added
- CLI options for the transfer command (#1675)

## [24.0.6] - 2023-01-19
### Fixed
- Set memory for each sample. Not just once. (#1711)

## [24.0.5] - 2023-01-18
### Added
- Tests (#1707)
### Fixed
- Set SLURM memory according to number of reads (#1707)

## [24.0.4] - 2023-01-16
### Changed
- MIP-DNA clinical delivery of delivery reports (#1703)

## [24.0.3] - 2023-01-16
### Added
- Dry-run option for store-housekeeper (#1686)
### Fixed
- Dry-run option for store (#1686)

## [24.0.2] - 2023-01-13
### Added
- Dry-run option for `config-case` (#1685)
### Fixed
- Dry-run for `cg workflow rnafusion run` does not set the action as `running` (#1685)

## [24.0.1] - 2023-01-12
### Changed
- Resume flag set as default for rnafusion run (#1684)

## [24.0.0] - 2023-01-12
### Changed
- Add SLURM resource allocation via cg config (#1696)
- Add hours to CLI for fastq compression (#1696)
- Changed flowcell CLI cmd to flow-cell (#1696)
### Fixed
- Correct setting of Crunchy SLURM allocation in Compress API (#1696)

## [23.8.2] - 2023-01-12
### Added
- Launch directory where the `.nexflow` directory is created (#1676)
- Export of NXF_PID_FILE variable to specify where the nextflow pid file is created (#1676)

## [23.8.1] - 2023-01-11
### Fixed
- Unbound variable error in fetching flow cell (#1699)

## [23.8.0] - 2023-01-10
### Added
- Multiple encrypt dir options (#1694)

## [23.7.3] - 2023-01-09
### Changed
- Updated list of balsamic validation cases | patch

## [23.7.2] - 2023-01-09
### Added
- Filter for status (#1695)
### Changed
- FLOWCELL_STATUS now only contains strings (#1695)

## [23.7.1] - 2022-12-29
### Changed
- CASE_ACTIONS is still defined via the CaseActions StrEnum but now only contains its values. (#1690)

## [23.7.0] - 2022-12-23
### Changed
- RML samples now pass sequencing qc as long as they have reads (#1688)

## [23.6.4] - 2022-12-20
### Changed
- Removed usage of alive_bar (#1681)
- Removed alive_progress as a dependency (#1681)

## [23.6.3] - 2022-12-19
### Fixed
- Moved the `RnafusionFastqHandler` to the bottom and re-added the methods to `RnafusionFastqHandler` (#1678)

## [23.6.2] - 2022-12-17
### Added
- Check to see if files already exists in bundle or not (#1677)

## [23.6.1] - 2022-12-15
### Added
- CG integration of nf-core rnafusion pipeline. (#1541)

## [23.6.0] - 2022-12-15
### Added
- Check to see if file exists before rsync (#1650)
- New --force-all flag to the deliver command to overwrite the rule below (#1650)
### Changed
- Do not deliver samples where sample.sequencing_qc is `False` (#1650)
- Removed qc-threshold for storing FASTQ-cases (#1650)

## [23.5.0] - 2022-12-15
### Fixed
- Fix(admin view) Made tickets filterable and added new batch options (#1664)

## [23.4.0] - 2022-12-15
### Added
- Loqusdb files passed to BALSAMIC when executing the `config case` command. (#1561)
- Swegen reference file (#1561)
- Balsamic automatic Loqusdb uploads (#1561)
### Fixed
- Empty family ticket causing trailblazer fails (#1561)

## [23.3.6] - 2022-12-13
### Added
- Reviewer files to scout load config (#1658)

## [23.3.5] - 2022-12-13
### Changed
- Do not compress Fluffy validation case (#1637)

## [23.3.4] - 2022-12-13
### Added
- Include cgstats log files in HK (#1644)
- Add tests (#1644)
### Changed
- Refactor meta/transfer (#1644)
- Include sequencing files in HK (#1644)
- Compress/decompress files with hard linka (#1644)

## [23.3.3] - 2022-12-12
### Changed
- Update last docker action (#1663)

## [23.3.2] - 2022-12-12
### Changed
- Update docker action (#1662)

## [23.3.1] - 2022-12-12
### Changed
- GitHub python action versions (#1661)

## [23.3.0] - 2022-12-08
### Added
- When an analysis is uploaded, trailblazer is updated with an uploaded at date (#1647)

## [23.2.6] - 2022-12-08
### Changed
- Update checkout action (#1656)
- Update setup python action (#1656)

## [23.2.5] - 2022-12-07
### Added
- Add bwa-mem option to mip analysis workflow (#1652)

## [23.2.4] - 2022-12-01
### Changed
- Deployment instructions (#1651)
- Be explicit with coveralls version in GitHub actions (#1651)

## [23.2.3] - 2022-12-01
### Changed
- Always use conda run when using crunchy (#1638)

## [23.2.2] - 2022-12-01
### Changed
- Parsing and correctly summerizing meanQscore (#1646)

## [23.2.1] - 2022-11-29
### Added
- Add a separate function to list modifiable keys in cg set (#1630)
- Add tests for new function (#1630)
### Changed
- Move relevant information in the custom help message of "cg set sample --help" to the click help message (#1630)
- Modify naming of sample_obj to sample in cli set base commands (#1630)

## [23.2.0] - 2022-11-28
### Changed
- Clean single sample microsalt cases (#1642)

## [23.1.1] - 2022-11-24
### Added
- Add -p flag to rsync command in cg to preserve permissions in Caesar

## [23.1.0] - 2022-11-23
### Changed
- Balsamic observations upload (#1632)

## [23.0.0] - 2022-11-22
### Added
- New command to post-process Hiseq X flow cells (#1621)
- Add cg transfer flow cell call to post processing of Novaseq and Hiseq X flow cells (#1621)
- Refactor flowcell to flow_cell (#1621)
### Changed
- Use cg transfer cmd directly from cg for Novaseq flow cells (#1621)

## [22.91.0] - 2022-11-21
### Added
- New delivery option: no-delivery (#1639)
### Changed
- The families function now accepts the data_delivery argument which filters on the given data_delivery (#1639)

## [22.90.3] - 2022-11-17
### Fixed
- Number of rows skipped when reading ins sample sheet (#1628)

## [22.90.2] - 2022-11-16
### Changed
- Removed split on spaces for the library prep and sequencing method document string for the microsalt typing report (#1634)

## [22.90.1] - 2022-11-15
### Fixed
- Raise error when no DNA samples linked to RNA subject_id. (#1589)
- DNA samples to upload to are filtered by application type and then by pipeline. (#1589)

## [22.90.0] - 2022-11-14
### Added
- Add ticket number to trailblazer (#1629)

## [22.89.2] - 2022-11-11
### Fixed
- Fix #1620 - Add panels for Michela (#1622)

## [22.89.1] - 2022-11-10
### Changed
- Remove app shipping (#1623)

## [22.89.0] - 2022-11-09
### Changed
- Adding clinical delivery to balsamic upload (#1626)

## [22.88.0] - 2022-11-09
### Added
- Balsamic mock observations API (#1603)
### Changed
- Observation API: split into MIP-DNA and BALSAMIC (#1603)
### Fixed
- Delete observations for different Loqusdb instances (#1603)

## [22.87.0] - 2022-11-03
### Changed
- Hotfix for adding barcode mismatch settings to samplesheet (#1619)

## [22.86.0] - 2022-11-02
### Changed
- Adding clinical delivery to mip-dna upload (#1611)

## [22.85.6] - 2022-11-01
### Changed
- Fixing parsing metrics that was moved during software dragen update (#1613)

## [22.85.5] - 2022-11-01
### Added
- Add multiQC report to rna delivery (#1612) | minor

## [22.85.4] - 2022-10-26
### Added
- Add all gene panels to mip analysis (#1606)

## [22.85.3] - 2022-10-25
### Added
- Support for the LIMS steps using the new Atlas method documents. (#1590)
- New constants for which type of documentation is used (AM or Atlas). (#1590)
- New function to get which method type has been used for a process. (#1590)
- New function to get a list of parent processes from a list of lims artifacts. (#1590)
- Support for RNA preps. (#1590)
### Changed
- Get method doc functions can now fetch Atlas docs in the form: <atlas doc name> (<atlas version>). (#1590)
- Renamed some functions solely used with the main get method function. (#1590)

## [22.85.2] - 2022-10-21
### Changed
- Change default gene panel for MAF cases from None to OMIM-AUTO (#1585)

## [22.85.1] - 2022-10-21
### Added
- Cg-dragen specification in dragen scripts (#1604)

## [22.85.0] - 2022-10-20
### Added
- A function to clean microsalt run directories (#1577)
### Changed
- Made the clean_run_dir in commands more atomic and moved out its functionality to respective API (#1577)
### Fixed
- Error raising for file not found so cleaned at date would be added and hopefully stop systemd timers complaining, (#1577)

## [22.84.6] - 2022-10-13
### Added
- Adds a new maintenance qos (#1578)
- Adds new function to hk_api for getting the last version of a bundle or logging that none were found (#1578)
### Changed
- Use it for SPRING to FASTQ compressions (#1578)
### Fixed
- Refactor tests (#1578)

## [22.84.5] - 2022-10-10
### Changed
- Catch loqus upload exceptions (#1595)

## [22.84.4] - 2022-10-10
### Fixed
- Fix(Error message) Added error message to CgError, fixes #1593 (#1594)

## [22.84.3] - 2022-10-10
### Fixed
- Exception handling for samples present in loqusdb (#1591)

## [22.84.2] - 2022-10-10
### Changed
- PrepCategory as string value (#1592)

## [22.84.1] - 2022-10-06
### Changed
- Delivery report sample name and sex retrieved from StatusDB and not LIMS. (#1588)
### Fixed
- Delivery report for downsampled analysis. (#1588)

## [22.84.0] - 2022-10-06
### Changed
- Observations CLI (#1567)
- Delete observations CLI (#1567)

## [22.83.1] - 2022-10-06
### Fixed
- Fixes logging of error messages (#1575)

## [22.83.0] - 2022-10-05
### Added
- A new gene CH panel to the master list of gene panels used in the analyses (#1587)

## [22.82.0] - 2022-10-04
### Added
- Delete observations option to remove a case from LoqusDB: variants related to a case_id are removed from LoqusDB and the loqusdb_id in statusDB is reset to None (#1568)
### Changed
- Reset option has been removed and replaced by delete observations option (see above). (#1568)

## [22.81.5] - 2022-10-03
### Fixed
- Set upload_started_at for fastq cases (#1584)

## [22.81.4] - 2022-09-30
### Changed
- All Process objects that are instantiated in cg now use positional arguments (#1582)

## [22.81.3] - 2022-09-30
### Fixed
- Use named args instead of positional when calling Process (#1581)

## [22.81.2] - 2022-09-29
### Added
- Added alembic as a requirement, since we rely on it when changing the database (#1580)

## [22.81.1] - 2022-09-29
### Changed
- Supply None if not set in config (#1579)

## [22.81.0] - 2022-09-29
### Added
- Added optional use of Conda binary for processes using Conda environments. (#1573)

## [22.80.1] - 2022-09-28
### Changed
- Feat(RNA upload) allow for upload to multiple cases (#1548)

## [22.80.0] - 2022-09-27
### Added
- CLI command to deliver any case to the delivery server (#1537)
- Method to the Family class to parse its data_delivery field (#1537)
### Changed
- The auto-fastq cli command now calls the newly created function instead of the previous that was specific to fastq cases (#1537)

## [22.79.1] - 2022-09-27
### Changed
- Changed qc target from application target reads to expected reads (#1547)

## [22.79.0] - 2022-09-16
### Changed
- Append the new ticket number to the tickets column for the case/family (comma separated) (#1565)
- Set the action of the family to `analyze` (#1565)

## [22.78.9] - 2022-09-13
### Changed
- Add option to use a "--login" shell in SLURMAPI (#1562)

## [22.78.8] - 2022-09-12
### Added
- Automatic genotype upload balsamic (#1555)

## [22.78.7] - 2022-09-08
### Fixed
- Original_ticket is now set for rml samples as well (#1558)

## [22.78.6] - 2022-09-08
### Added
- A new test for MIP-dna, balsamic and RML json-orders (#1554)
- Created two new json file fixtures (#1554)

## [22.78.5] - 2022-09-08
### Fixed
- Delivery report complaining about a missing `received_at` field (#1556)
- Float zero values appearing as `N/A` in the delivery report (#1556)

## [22.78.4] - 2022-09-05
### Fixed
- Added missing query assignment for analyses to upload retrieving (#1550)
- Delivery report generation as part of the upload command (#1550)

## [22.78.3] - 2022-09-05
### Fixed
- Put `original_ticket` in the searchable columns field (#1552)

## [22.78.2] - 2022-09-02
### Added
- The VCFs uploaded to Scout are now displayed in the delivery report (#1536)
- Version of BALSAMIC tools added to the report (#1536)
### Changed
- Simplified delivery report CLI (#1536)
- Decoupled delivery report from LIMS delivery (#1536)
- The report generation and upload to Scout has been separated (https://github.com/Clinical-Genomics/cg/issues/1457). (#1536)
- Delivery report creation is triggered by the availability of files in HK (#1536)
- The upload is only triggered when the delivery report has been generated (#1536)
- The delivery report is being uploaded as part of the main upload (`cg upload -f`) (#1536)
- Updated upload & delivery report status queries (#1536)

## [22.78.1] - 2022-09-01
### Added
- Json api (#1543)
- Json to io controller (#1543)
- Test for json controller and json_api (#1543)
### Changed
- Use generic io controller to read json files. One exception that I did not dare touch is `cg/apps/cgstats/db/models/base.py` as I do not understand this code and it seems like it is moved from cgstats. I think it would be best to fix that in a cgstats focused PR. (#1543)
### Fixed
- Refactored a lot of hard coded paths in the test suite (#1543)

## [22.78.0] - 2022-08-31
### Added
- Tickets column to family table (#1534)
### Changed
- Renamed ticket_number column in the sample table to original_ticket (#1534)
- Changed the type of the column to Varchar(128)/string. (#1534)
- Refactored usage from ticket_number/ticket_nr/ticket_id to just ticket (#1534)
- Changed functions that access ticket via sample to instead go via family (#1534)

## [22.77.2] - 2022-08-24
### Added
- Module to reuse SQL filtering operations (#1545)
- Add test for module above (#1545)
### Changed
- Split query to separate function (#1545)
- Refactor cases_to_analyze to use filtering functions instead of hard coded filtering operations (#1545)
- Refactor tests (#1545)
- Moved utility function to helper class for future reuse (#1545)

## [22.77.1] - 2022-08-23

## [22.77.0] - 2022-08-23
### Added
- Reference genome attribute to 1508samples (#1529)
- New delivery options (#1529)
### Changed
- Changes all the uses of "analysis-bam" to "analysis", "fastq_qc-analysis-cram" to "fastq-analysis" and "fastq_qc-analysis-cram-scout" to "fastq-analysis-scout" (#1529)
- Changes the Column type from an ENUM to VARCHAR in the database. The python models still use the enum (#1529)

## [22.76.1] - 2022-08-17
### Changed
- Remove cli and tests (#1538)

## [22.76.0] - 2022-08-12
### Changed
- Update codeowners (#1539)

## [22.75.5] - 2022-08-12
### Added
- Add new cases to the compression exclusion list (#1542)

## [22.75.4] - 2022-08-05
### Added
- General Yaml API (#1524)
- General io controller for reading files and streams for yaml (and other file formats in the future) (#1524)
- Added test for yaml API (#1524)
### Changed
- Use general Io controller to read and write yaml files and streams (#1524)
### Fixed
- All yaml interactions are DRY (only defined and tested once and then reused) (#1524)
- Yaml is only imported once in the entire code base and interaction is fully tested. Hence, easy to update and change in the future. (#1524)

## [22.75.3] - 2022-08-05
### Changed
- Do not compress external data (#1519)

## [22.75.2] - 2022-08-05
### Added
- Balsamic PON workflow (#1533)

## [22.75.1] - 2022-08-05
### Fixed
- Update coverall action (#1535)

## [22.75.0] - 2022-07-20
### Fixed
- Handle nanopore fastq headers (#1527)

## [22.74.1] - 2022-07-20
### Fixed
- Validation of existing samples now works as intended (#1530)

## [22.74.0] - 2022-07-18
### Changed
- Do not check number of reads for nanopore (external data) (#1526)

## [22.73.0] - 2022-07-13
### Changed
- App tags for external samples are now returned under two keys in the dict returned by the options endpoint (#1523)

## [22.72.0] - 2022-07-12
### Added
- Link table between customers and collaborations (#1520)
- Allows customers to be part of multiple collaborations (#1520)
### Changed
- Renamed customer groups to collaborations (#1520)

## [22.71.1] - 2022-07-08
### Changed
- Remove/replace pg (#1509)

## [22.71.0] - 2022-07-05
### Added
- Balsamic UMI analysis-workflow (#1493)
- Balsamic UMI Scout/delivery report upload (#1493)
- Balsamic QC analysis workflow (#1493)
- Gender parsing for balsamic cases (#1493)

## [22.70.1] - 2022-07-04
### Changed
- Lowers QG treshold for loqusdb load (#1514)

## [22.70.0] - 2022-06-30
### Added
- Email to be sent when connecting a new order to an existing ticket (#1505)

## [22.69.0] - 2022-06-29
### Changed
- Refactor constants to config and regexp path extraction for long-term-storage retrieval (#1517)

## [22.68.1] - 2022-06-29
### Fixed
- Added validation of cost_center against "KTH" or "KI" to fix path injection vulnerability (#1512)

## [22.68.0] - 2022-06-28
### Added
- Possibility to use the genotype apis on balsamic cases. (#1508)

## [22.67.1] - 2022-06-28
### Changed
- Config via cli (#1513) minor

## [22.67.0] - 2022-06-28
### Added
- Support fastq linking for mutant with nanopore (#1499)

## [22.66.0] - 2022-06-27
### Changed
- Migrate fetching archived flow cells from NAS-9 to Hasta (#1486)

## [22.65.1] - 2022-06-23
### Fixed
- Typo in excel orderform parsing (#1511)

## [22.65.0] - 2022-06-22
### Changed
- Added Field Primer in Lims (#1487)

## [22.64.0] - 2022-06-14
### Changed
- Add comment to sample (#1507)

## [22.63.3] - 2022-06-10
### Changed
- VJ added as codeowner (#1504)

## [22.63.2] - 2022-06-09
### Changed
- Fetches analyses to delivery reports & analysis to upload (balsamic) by data delivery (#1502)

## [22.63.1] - 2022-06-09
### Changed
- Track cases considered converted and do not try to compress cases without samples (#1506)

## [22.63.0] - 2022-06-08
### Changed
- Fastqsubmiter now creates just one case for the order and assigns the correct customer. (#1494)
- For non-tumor WGS samples a second case is created for MAF purposes. (#1494)

## [22.62.3] - 2022-06-07
### Changed
- Refactoring(structure): Move case fields from sample to case (#1497)

## [22.62.2] - 2022-06-03
### Changed
- Set external reference via cli in Fluffy (#1501) minor

## [22.62.1] - 2022-06-01
### Changed
- Delivery report query: retrieving analyses only for a specific pipeline (#1498)

## [22.62.0] - 2022-06-01
### Added
- Attaches json file of order to ticket (#1496)

## [22.61.5] - 2022-05-31
### Added
- New pipeline specific upload APIs (MIP-DNA & BALSAMIC) (#1488)
### Changed
- `cg upload ...` CLI behaviour (#1488)

## [22.61.4] - 2022-05-25
### Changed
- Updated OF 1604:14 to 1604:15 (#1489)
- Updated excel fixture for 1604 (#1489)

## [22.61.3] - 2022-05-23
### Fixed
- Fix(scout config) Revert back to strings (#1492)

## [22.61.2] - 2022-05-22
### Changed
- Representation of the types Gender and PhenotypeStatus (#1490)

## [22.61.1] - 2022-05-19
### Added
- Add test for new diagnosis_phenotype model (#1464)
### Changed
- Changed pydantic model for diagnosis_phenotypes to DiagnosisPhenotypes (#1464)
- Refactored and use more constants (#1464)

## [22.61.0] - 2022-05-19
### Added
- `balsamic-umi` delivery option (#1477)
- `vcf2cytosure` upload to Scout (#1477)
- `--pon-cnn` config case flag for BALSAMIC (#1477)
- `--genome-version` config case flag for BALSAMIC (#1477)
### Changed
- Balsamic delivery tags (#1477)

## [22.60.0] - 2022-05-18
### Added
- New function for findbusinessdata `get_case_pool` which returns the pool connected to a case if any. (#1463)
### Changed
- The command `cg workflow fastq store-available` now has an extra if clause where it only stores cases that are pools or non-rml cases where all samples have been sequenced and pass QC. (#1463)

## [22.59.0] - 2022-05-16
### Added
- Added the use of data_delivery for metagenomes (#1485)
- Added validation of unique sample names for metagenomes (#1485)
### Changed
- Changed the way cases are created for metagenomes (#1485)
- Changed the structure of the status_data dict (#1485)
- Refactored microbial_submitter (#1485)

## [22.58.0] - 2022-05-12
### Changed
- Fetch mip files from HK using multiple tags (#1260)

## [22.57.5] - 2022-05-10
### Added
- New selection criteria sarscov2 orderform (#1470) minor

## [22.57.4] - 2022-05-09
### Fixed
- Fix/missing-backup-api-meta-api (#1480)

## [22.57.3] - 2022-05-06
### Changed
- List of cases balsamic validation cases (#1473)
- EncryptionAPI - CodeFactor fix (#1473)

## [22.57.2] - 2022-05-05
### Fixed
- Fix set dry run (#1479)

## [22.57.1] - 2022-05-05
### Changed
- Move require_qcok from family to sample (#1478)

## [22.57.0] - 2022-05-05
### Added
- Spring encryption and PDC archiving (#1455)
- Spring decryption and PDC retrieval (#1455)

## [22.56.3] - 2022-05-04
### Fixed
- Except TicketCreationError in other function to prevent an order being placed if it is raised (#1476)

## [22.56.2] - 2022-05-04
### Changed
- Change config via cli for fluffy (#1475) minor

## [22.56.1] - 2022-05-02
### Added
- Support OF 1508:26 (#1466)

## [22.56.0] - 2022-04-28
### Changed
- Delivery report for BALSAMIC (#1446)

## [22.55.1] - 2022-04-22
### Fixed
- Fix(DeliverAPI) Support for multiple customer and tickets per instance

## [22.55.0] - 2022-04-22
### Fixed
- Fix(BalsamicAnalysisAPI) change cases_to_store from finish-file to tb-check (#1468)

## [22.54.12] - 2022-04-22
### Fixed
- Consistently round invoiced values at all stages of discount calculation (#1469)

## [22.54.11] - 2022-04-19
### Changed
- Fohm request (#1454)

## [22.54.10] - 2022-04-13
### Changed
- Changed the `cg upload` command so that the upload scout part is put behind an if clause. (#1461)

## [22.54.9] - 2022-04-13
### Added
- HS as code owner (#1462)

## [22.54.8] - 2022-04-07
### Changed
- Change/required fields for delivery report (#1456)

## [22.54.7] - 2022-04-05
### Changed
- MIP-DNA delivery report workflow (#1438)

## [22.54.6] - 2022-04-05
### Added
- A store and store-available command to create analyses for fastq-cases (#1449)
- An upload case and upload alll-available command to deliver the fastq files to caesar (#1449)

## [22.54.5] - 2022-04-04
### Added
- New twist workflow -> new bait set step (#1453)

## [22.54.4] - 2022-04-01
### Changed
- Changed qos for clinical trails (#1450) | minor

## [22.54.3] - 2022-04-01
### Fixed
- Basemask generation from RunInfo.xml (#1448)

## [22.54.2] - 2022-03-29
### Changed
- Q30 check in demultiplexing generalised for NovaSeq (#1444)

## [22.54.1] - 2022-03-29
### Fixed
- Error messages from orderform validation contain quotes around the value in order to improve comprehension (#1447)

## [22.54.0] - 2022-03-29
### Changed
- Match tumour-state for RNA (#1433)

## [22.53.0] - 2022-03-28
### Added
- Price clinical_trials field for ApllicationVersion (#1445)
### Changed
- Prices in ApplicationVersion now editable (#1445)

## [22.52.0] - 2022-03-25
### Added
- Flow cell name tag when adding fastq files back to hk (#1402)

## [22.51.0] - 2022-03-25
### Changed
- Validate length of organism name (#1441)

## [22.50.0] - 2022-03-24
### Added
- A function to rsync single cases to caesar (#1422)
### Changed
- The rsync command written to the slurm scripts (#1422)

## [22.49.2] - 2022-03-23
### Added
- Support RML OF 1604:14 (#1439)

## [22.49.1] - 2022-03-23
### Added
- API for deletion of flow cells (#1323)

## [22.49.0] - 2022-03-21
### Changed
- Feat (slurm) Use qos express (#1415)

## [22.48.1] - 2022-03-15
### Changed
- Continue bundle-cleaning when bundles are missing (#1435)

## [22.48.0] - 2022-03-15
### Added
- Add tags to protect for FLUFFY (#1434)

## [22.47.1] - 2022-03-09
### Changed
- Remove avatars (#1424)

## [22.47.0] - 2022-03-09
### Changed
- Search sample by subjectId (#1423)

## [22.46.6] - 2022-03-08
### Changed
- File storage of balsamic cases with failed QC (#1430)

## [22.46.5] - 2022-03-08
### Changed
- Remove most old case bundle files (#1418)

## [22.46.4] - 2022-03-03
### Added
- Added star fusion and arriba reports to mip-rna delivery. (#1429)

## [22.46.3] - 2022-03-02
### Changed
- Updated function sequencing_qc (#1417)

## [22.46.2] - 2022-03-02
### Fixed
- Previous index is now dropped when reset (#1428)

## [22.46.1] - 2022-02-25
### Fixed
- Fix/fohm pandas indices (#1421)

## [22.46.0] - 2022-02-16
### Changed
- PR Template (#1413)
### Fixed
- Missing release tag (#1413)

## [22.45.1] - 2022-02-16
### Added
- Support new orderform column "Delivery" with options: "fastq" and "Statina" (#1412)
- Support new orderform option "No analysis" for "Data Analysis" (#1412)
- Support new orderform column "Control sample" (#1412)
- Support RML Indices TWIST UDI SET B (#1412)
- Support RML Indices TWIST UDI SET C (#1412)

## [22.44.5] - 2022-02-16
### Fixed
- Remove an insecure user controlled data from logging on order submit (#1411)

## [22.44.4] - 2022-02-15
### Fixed
- Revert "Feat(Orderportal): Support new RML OF (#1401) (minor)"
- Revert "Bump version: 22.44.3 → 22.45.0 [skip ci]"
- Fixed the force upload of NIPT cases (#1409)

## [22.45.0] - 2022-02-14
### Added
- Support new RML OF (#1401)

## [22.44.3] - 2022-02-09
### Added
- Add: upload BALSAMIC CNV report to Scout (#1384)

## [22.44.2] - 2022-02-07
### Fixed
- Handle flow cell not in statusdb (#1394)

## [22.44.1] - 2022-02-03
### Changed
- Use correct exception (#1388)

## [22.44.0] - 2022-02-03
### Changed
- Utilize auth of statina api v2 for load (#1392)

## [22.43.2] - 2022-02-02
### Changed
- Statina method update

## [22.43.1] - 2022-02-02
### Changed
- Don't remove flow cells (being) retrieved from PDC (#1391)

## [22.43.0] - 2022-02-01
### Added
- NIPT QC-check functions prior upload and latest flow cell usage (#1380)

## [22.42.0] - 2022-01-31
### Added
- Support OF 1603:11 (#1386)

## [22.41.3] - 2022-01-28
### Added
- Threshold constant for a flow cells q30 depending on their read length (#1345)

## [22.41.2] - 2022-01-27
### Added
- Adds more unit test to MIP CLI (#1248)
### Changed
- Better error handling for MIP CLI (#1248)

## [22.41.1] - 2022-01-24
### Changed
- Clean flow cell run only check directories (#1376)

## [22.41.0] - 2022-01-21
### Changed
- Clean flow cell run directories (#1371)

## [22.40.5] - 2022-01-21
### Changed
- Quick fix to allow missing volume for existing samples (#1373)

## [22.40.4] - 2022-01-18
### Changed
- Check exhausts generator (#1368)

## [22.40.3] - 2022-01-18
### Changed
- Skip sample sheet archiving if no unaligned dir exists (#1367)

## [22.40.2] - 2022-01-18
### Changed
- Check and remove in parallel (#1366)

## [22.40.1] - 2022-01-17
### Fixed
- Fix double passed check of some flowcells (#1365)

## [22.40.0] - 2022-01-17
### Changed
- Archive sample sheets on hasta and in Housekeeper when cleaning demultiplexed-runs (#1363)

## [22.39.1] - 2022-01-14
### Added
- Support OF 1604:12 (#1364)

## [22.39.0] - 2022-01-13
### Added
- Allow customer to delete file on caesar (#1362)

## [22.38.3] - 2022-01-12
### Changed
- Priority as enum (#1352)

## [22.38.2] - 2022-01-12
### Fixed
- Fix clean demux permission error and query filter (#1361)

## [22.38.1] - 2022-01-11
### Added
- Add bcl_converter flowcell creation (#1360. patch)

## [22.38.0] - 2022-01-11
### Changed
- Check demultiplexed runs (#1334)

## [22.37.4] - 2022-01-04
### Fixed
- Fix/external rsync caesar (#1356 patch)

## [22.37.3] - 2022-01-04
### Fixed
- Fix/external-rsync-caesar (#1355 minor)

## [22.37.2] - 2021-12-31
### Added
- Add/BALSAMIC ascat, manta, cnvkit, delly tags for delivery (#1354)

## [22.37.1] - 2021-12-14
### Changed
- Skip analysis for external until "analyze" (#1347)

## [22.37.0] - 2021-12-14
### Added
- Added express threshold for automatic start in mip and balsamic (#1332)

## [22.36.1] - 2021-12-13
### Added
- Can now parse and upload samples with existing GISAID ID to FOHM (#1349)

## [22.36.0] - 2021-12-13
### Added
- A check so that only cases that are present in our cluster and do not already have an analysis are started. (#1335)
### Changed
- Some larger functions have been split. (#1335)

## [22.35.0] - 2021-12-13
### Added
- Possibility to mark Microsalt and Sarscov2 samples as controls (#1302)
- Check that sarscov2 sample names are unique unless they are controls (#1302)

## [22.34.4] - 2021-12-10
### Fixed
- Strip indexes of any whitespaces (#1348)

## [22.34.3] - 2021-12-09
### Changed
- Calculate correct sample.is_external (#1309)

## [22.34.2] - 2021-12-08
### Changed
- Updated authors (#1343) patch

## [22.34.1] - 2021-12-08
### Fixed
- Lets JSON orders have line breaks in string values

## [22.34.0] - 2021-12-07
### Changed
- Family view: (#1338)
- Hide columns: "created_at", "_cohorts", "synopsis"] (#1338)
- Hide form fields: "analyses", "cohorts", "links", "synopsis" (#1338)
- Sample view: (#1338)
- Hide columns: "age_at_sampling", "invoiced_at", "_phenotype_groups", "_phenotype_terms" (#1338)
- Hide form fields: "age_at_sampling", "deliveries", "father_links", "flowcells", "invoiced_at", "invoice", "is_external", "_phenotype_groups", "_phenotype_terms", "links", "mother_links" (#1338)
### Fixed
- Sample records fast to edit (#1338)
- Family records fast to edit (#1338)

## [22.33.0] - 2021-12-06
### Added
- A check so that only samples present on caesar are rsynced (#1327)
### Changed
- All samples are now rsynced in the same SLURM-job (#1327)

## [22.32.2] - 2021-12-03
### Changed
- Log unauthorized login attempts (#1339)

## [22.32.1] - 2021-11-29
### Changed
- Accept optional empty/missing numerical values in json (#1333)

## [22.32.0] - 2021-11-26
### Changed
- Validate with pydantic (#1313)

## [22.31.7] - 2021-11-25
### Added
- Control field in list of UDFs to set when creating a order. (#1329)

## [22.31.6] - 2021-11-24
### Added
- Henning as codeowner (#1330)

## [22.31.5] - 2021-11-23
### Fixed
- More logging for fohm upload (#1328)
- Drop non-unique now ignores index when uploading to fohm (#1328)

## [22.31.4] - 2021-11-22
### Fixed
- Regex for fohm upload (#1326)

## [22.31.3] - 2021-11-22
### Added
- Showing sample comment when creating new invoice for samples (#1325)

## [22.31.2] - 2021-11-22
### Changed
- Remove escape regex

## [22.31.1] - 2021-11-16
### Fixed
- Search exact match search for sample name in fohm/gisaid logic (#1324)

## [22.31.0] - 2021-11-10
### Added
- Upload RNA files to Scout (#1305)

## [22.30.0] - 2021-11-10
### Added
- Support for RML OF 1604:11 with two new Indexes: TWIST UDI Set A and KAPA UDI NIPT (#1322)

## [22.29.3] - 2021-11-09
### Added
- Support 1604:11
### Fixed
- Revert "Support 1604:11"

## [22.29.1] - 2021-11-08
### Fixed
- Remove unneeded flag in unlink (#1320)
- Revert to python 3.6 in setup.py (#1320)

## [22.29.0] - 2021-11-08
### Changed
- Cg clean hk-bundle-files refactored: (#1315)
- Will clean bundles older than x days (#1315)
- Will filter by pipeline as criteria (#1315)
- Will accept multiple tags as criteria (#1315)
- WIll accept case_id as criteria (#1315)
- WIll clean all bundles, not just latest bundles (#1315)

## [22.28.0] - 2021-11-04
### Changed
- Added md5sum ckecks (#1272)

## [22.27.0] - 2021-11-02
### Changed
- More flexible regex for checking sars-cov sample name (#1312)
- Re-use upload log no matter what bundle version it is in (#1312)
