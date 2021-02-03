# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.0.0/)

Please add a new candidate release at the top after changing the latest one. Feel free to copy paste from the "squash and commit" box that gets generated when creating PRs

Try to use the following format:

## [x.x.x]

### Added
### Changed
### Fixed

## [NG.NG.NG]

### Added
- Support for storing cohorts, phenotype_terms and synopsis from order json

## [18.10.0]

### Added
- Support for delivery type in the Order Portal

## [18.9.1]

### Added
- cg upload vogue bioinfo-all uploads both BALSAMIC as well.

## [18.9.0]

### Added

- Add functionality to upload balsamic analyses to scout

## [18.8.0]

### Added
- cg workflow microsalt upload-analysis-vogue [case_id] to upload the latest analysis from specific case
- cg workflow microsalt upload-latest-analyses-vogue to upload all latest analyses what haven't been uploaded

## [18.7.2]

### Changed

- Skip deliver fastq files when delivering balsamic analysis

## [18.7.1]

### Fixed

- clean_fastq command now also skips validation cases when cleaning fastq files

## [18.7.0]

### Added
- Added customer name in order tickets

## [18.6.1]

### Fixed

- Fix bug with name clash for created case when submitting RML-orders via Orderportal


## [18.6.0]


### Added

- Add command 'delete case' to remove case from the database
- Add command 'delete cases' to remove multiple cases from the database

## [18.5.1]

### Fixed

- Fix bug with microsalt deliverables path where it only returns the path only if it exists. This caused errors in some cases when submitting to Trailblazer

## [18.5.0]

### Added
- Added MHT to gene panel master-list

## [18.4.0]

### Added

- Added submission of microsalt cases for tracking in Trailblazer

## [18.3.0]

### Changed

- cg workflow mip-dna --panel-bed and --dry-run options can be set when executing full workflow
- Changed logic for how case links are retrieved in order to support linking of very old cases
- Analysis not submitted to Trailblazer if executing MIP workflow in dry-run

## [18.2]

### Changed

- Remove option to specify delivery path when delivering data

### Fixed

- Improved usage of `cg deliver analysis` command

## [18.1.5]

### Fixed

- cg workflow mip-rna link command

## [18.1.4]

### Fixed

- Better help text for microsalt cli commands


## [18.1.3]

### Fixed

- deliver filtered cnvkit file for balsamic

## [18.1.2]

### Fixed

- cg workflow mip-rna config-case command
 
## [18.1.1]

### Fixed

- Updates balsamic deliver tags to align with the ones specified in hermes

## [18.1.0]

### Added
- Customer in the ticket created for an order from the Orderportal

## [18.0.0]

### Added
- New commands for running cron jobs 

### Changed
- Changed cli commands for starting and storing microsalt workflows

### Fixed
- Full Microsalt can now be executed through cg interface

## [17.2.1]

### Fixed

- HermesApi added to context when running cg clean

## [17.2.0]

### Changed

- Using HermesApi to save Balsamic deliverables in Housekeeper

## [17.1.0]

### Added

- Added support for Balsamic-orderforms as json-file

### Changed

## [17.0.0]

### Added
- Lims ID is sent to Balsamic during case config

## [16.17.1]

### Fixed
- Fixed exporting reduced mt_bam to scout config

## 16.17.0

### Changed
- Update Scout config output for images from chromograph

## 16.16.1

### Fixed

- This PR fixes the problem handling wells in json orders without ":" as separator, e.g. A1 instead of A:1

## [16.16.0]

### Changed

- Use hermes for generating balsamic deliverables

## 16.15.1

### Fixed
- The problem handling mip-json without specified data_analysis

## [16.16.0]

### Added

- Validation models for excel files in `cg/store/api/import_func.py`

### Fixed

- Removes dependency on deprecated excel-parser `xlrd`


## 16.15.0

### Added
- cg deploy hermes

## 16.14.0

### Added
- cg deploy fluffy


## 16.13.0

### Added

- Stop on bad values for analysis (pipeline) when adding family through CLI

## 16.12.1

### Fixed
- Save in Family and Analysis Admin views

## 16.12.0

### Added

- Added support for RML-orderforms as json-file

## [16.11.1]

### Fixed

- Lock dependency for xlrd so that we can parse modern excel files


## 16.11.0

### Added
- cg set family [CASEID] now has the option --data-delivery

## [16.10.4]

### Fixed
- Bug when building tag definition for balsamic-analysis delivery

## [16.10.3]

### Fixed
- Use `--json` when exporting causative variants from scout

## [16.10.2]

### Fixed
- Use correct pipeline name when cleaning mip analysis dirs

## [16.10.1]

### Added

- Adds new mip-dna tags to hk

## [16.10.0]

### Added

- Adds new delivery type to balsamic-analysis

## [16.9.0]

### Added

- column percent_reads_guaranteed to application table

## [16.8.1]

### Fixed

- Bug in the interactions with Scout when cleaning Scout cases
- Bug in the interaction with scout in command export_causatives

## [16.8.0]

### Added

- Adds adding samplesheet to HK flowcell bundle to cg transfer flowcell

## [16.7.1]

### Fixed

- Mutacc looks for 'id' instead of '_id' in case export
- Convert 'other' to '0' for sex in case export

## 16.7.0

### Added
- Show sample priorities in created ticket

## [16.6.0]

### Changed

- Split generating config into its own command
- Delete old load config when running `cg upload scout --re-upload`

## [16.5.0]

### Added

- Functionality to deploy scout with cg

## [16.4.3]

### Fixed

- Bug that madeline output files where not uploaded to scout
- Bug when exporting panels with `cg workflow mip-dna panel`

## [16.4.2]

### Fixed

- Bug that display_name was used instead of sample_name

## [16.4.1]

### Fixed

- Change compression query to be both satisfactory syntax for flake and to be working on our version of sql server

## [16.4.0]

### Added
- Use Pydantic models to validate Scout input/output

### Changed
- Decouples scout from CG

## [16.3.4]

### Fixed

- Fixed documentation on Trailblazers purpose

## [16.3.3]

### Fixed

- Fixed setting of priority in statusDB and LIMS for samples

## [16.3.2]

### Fixed

- Fixed setting of apptag in LIMS for samples

## [16.3.1]

### Fixed

- Fixed a bug in naming of "default_gene_panels" in Scout load config


## [16.3.0]

### Changed
- Changed logic for which cases are to be compressed. Now compression will be run on all cases older then 60 days provided their fastq files have not been decompressed less than 21 days prior


## [16.2.0]

### Changed

- Use CLI to upload to Scout

## [16.1.1]

### Fixed
- Accreditation logotype only shown on new delivery reports for accredited analyses


## [16.1.0]

### Changed
- Changed the way cg cleans cases. Now it only uses StatusDB and family status

### Added
- Added one-time script to iterate over mip directories, and set cleaned_at timestamp on very old cases that were already cleaned


## [16.0.6]

### Fixed
- 'cg upload auto --pipeline' to accept 'mip-dna' as pipeline

## [16.0.5]

### Fixed
- Trailblazer integration fixed

## [16.0.4]

### Fixed
- Case database entities (Family) can only have specific values for data_analysis
- Analysis database entities can only have specific values for pipeline
- Enum used for pipeline as arguments

## [16.0.3]

### Fixed
- Microbial config-case now correctly imports reference from customer provided reference

## [16.0.2]

### Added
- Added case intentmayfly to list of cases to except from SPRING compression

## [16.0.1]

### Added
- Updated PR template to include implementation plan

## [16.0.0]

### Added
- Deliver analysis based on case-id or ticket

### Changed
- Deliver commands merged into new command `cg deliver analysis`

## [15.0.4]
### Fixed
- fixed failing `cg microsalt store completed` cronjob

## [15.0.3]
### Fixed
- Fixed path where microsalt deliverables files are located

## [15.0.2]
### Fixed
- Wrap more cg workflow mip-dna store code in try-except in order to not cause future production blocks

## [15.0.1]
### Fixed
- Fix bug in compress clean command

## [15.0.0]

### Added
- New command: cg store ticket <ticket_id>
- New command: cg store flowcell <flowcell_id>
- New command: cg store case <case_id>
- New command: cg store sample <sample_id>

### Removed
- Old command: cg store fastq <case_id>

## [14.0.1]

### Fixed
- Removed unused options form cg workflow balsamic base command


## [14.0.0]

### Added
- New command: cg decompress ticket <ticket_id>
- New command: cg decompress flowcell <flowcell_id>
- New command: cg decompress case <case_id>
- New command: cg decompress sample <sample_id>

### Removed
- Old command: cg compress decompress spring <case_id>

## [13.18.0]


### Changed
- Changed condition for which cases should be stored in CG. This fixes a bug where cg would try to store cases which already have been stored due to mismatch in timestamp stored in Trailblazer and Housekeeper

## [13.17.2]

### Changed
- Only fastq files older than three weeks will be compressed


## [13.17.1]

### Added
- Added new value to lims constants
- Moved lims constants to a constants directory


## [13.17.0]


### Changed
- Workflow mip-dna store no longer needs analysisrunstatus to be completed to attempt storing bundle


## [13.16.2]

### Fixed

- Fixed bug where parse_mip_config() only returned values for primary analysis, breaking Upload Delivery Report


## [13.16.1]

### Fixed

 - Fix bug where cg workflow mip store still relied on Trailblazer to find case_config.yaml (Where it can no longer be found)
 - Fix bug where microsalt cli lost its store command in merge conflict


## [13.16.0]

### Added
- New REST-based TrailblazerAPI
### Changed
- Trailblazer support for Balsamic
### Fixed
- Naming convention for API harmonized


## [13.15.0]

### Added
- New query to get all cases in ticket

## [13.14.3]

### Changed

- Refactors constants file

## [13.14.2]

### Fixed

 - Fixed bug where CalledProcessError class could not be represented as string, and broke workflows.
 - Rephrased query used for compression. The query output is unchanged
 - Fixed typo in query name


## [13.14.1]
### Removed
- Remove data_analysis from sample since it is deprecated

## [13.14.0]
### Changed
- Move data_analysis from sample level to case level to enable samples to be analysed differently in different cases

## [13.12.0]
### Added
- Store all available completed microbial analyses in HK

## [13.11.0]

### Changed
- Balsamic always skips mutect when application is WES
- SPRING compression is set to run on oldest families first

### Fixed
- Format print statements

## [13.10.2]

### Fixed
- Storing chromograph, upd and rhocall files in housekeeper

## [13.10.1]

### Fixed
- Repaired automation query for storing Balsamic cases in Housekeeper

## [13.10]

### Added
- Functionality to deploy `genotype` with CG on hasta

### Fixed
- Stored completed not parsing through all completed entries

## [13.9]

### Added
- Deployment command
- Functionality to deploy `shipping` with CG


## [13.8.0]
### Added
- Functionality to change multiple families in one go, e.g. cg set families --sample-identifier ticket_number 123456 --priority research

## [13.7.0]
### Fixed
- Set flowcell status to `ondisk` when retrieving archived flowcell from PDC has finished.

## [13.6.0]

### Added
- Store microsalt analyses in Housekeeper with a provided deliverables file

## [13.5.0]

### Added
- Possibility to give case-id as argument when setting values on multiple samples by the CLI


## [13.4.1]


### Fixed
- Updated changelog with correct release version


## [13.4.0]

### Removed
- Microbial order table
- Microbial order model
- Microbial sample table
- Microbial sample model
- Microbial Flowcell-sample table
- Microbial Flowcell-sample model

### Changed
Show customer name instead of id in invoices view.
Made customer name searchable in invoices view.

### Fixed
Made unidirectional links to Customer (instead of bi) to speed up customer view
Made unidirectional links to ApplicationVersion (instead of bi) to speed up view

## [13.3.1]

### Changed
- Exclude analysis older than hasta in production (2017-09-27) from delivery report generation

## [13.3.0]

### Added
- Added new cases to skip during compression

## [13.2.0]

### Changed
- Only talk to genotype via subprocess and CLI


## [13.1.0]

### Changed
- Added cases for all microbial samples
- Add a case when a new microbial order is received

## [13.0.0]

### Changed
- Moved all microbial samples into samples table and the depending logic

## [12.7.1]

### Fixed
 - Removed store-housekeeper one-time script that was used to store balsamic results in Housekeeper

## [12.7.0]

### Changed
- Moved queries in TrailblazerAPI to Trailblazer

## [12.6.0]

### Added
- Added support for MIP9
- Adds support for MIP 9.0 files and tags in HK:
  - telomerecat
  - cyrius star-caller
  - smncopynumber caller on case level
  - tiddit_coverage bigwig track
- Adds smncopynumbercaller file to scout load config
### Changed
- Removed TB mip start source code from cg

### Fixed
- Return when using mip-dry-run option so that the dry-run is not added to TB

## [12.5.0]

### Changed

- Now ignores errors while cleaning old Balsamic data with cg clean


## [12.4.0]

### Added
- Providing a name of panel bed file in MIP cli now overrides getting capture kit through LimsAPI during case config
### Changed
- Providing panel bed path or capture kit shortname in BALSAMIC cli now overrides getting capture kit through LimsAPI during case config
### Fixed
- Fix Balsamic automation functions to exit with 1 if any of the errors are raised while looping through cases

## [12.3.6]

### Fixed
- Fixes bug where scout_api was sent into the compression_api in cli/store. The compression_api does not have scout_as an argument.


## [12.3.5]

### Added
- Added @Mropat as codeowner

## [12.3.4]

### Fixed
- Fixes bug where  upload_started_at and uploaded_at timestamps were not being updated in StatusDB upon successful Scout upload.
This bug was happening because several instances of Store were instantiated in the same context

## [12.3.3]

### Fixed
- Fixes but where linking MIP trio samples only linked the first sample instead of the whole family (Introduced in recent PR)
- Fixes bug where linking by SampleID was not linking the entire family (Old)
- Fixes bug where linking by SampleID would not be able to generate correct linking path (Old)

## [x.x.x]
### Added

### Fixed

### Changed


## [13.0.0]
### Changed
- Microbial Samples are now treated as ordinary samples in a case

## [12.3.2]

### Fixed

- Upload delivery report should now only happen for mip analyses
- Re-use the same API within all upload context
- Handle unspecified exceptions in order to keep the cron running when unexpected exception occurs for one case
- When linking file without data analysis set, warn about it and link file correctly

## [12.3.1]

### Fixed

- Fixed bug where AnalysisAPI in cg upload auto was not updated to recent class changes

## [12.3.0]

### Changed

- Class ConfigHandler moved from Trailblazer codebase into CG codebase
- FastqHandler methods moved from Trailblazer to AnalysisAPI
- Merged MipAPI and AnalysisAPI for mip_rna and mip_dna into one meta-api class
- Adjusted tests to support the new architecture
- Removed (unused/deprecated)run method which was used to execute MIP through Trailblazer

### Fixed

- MIP workflow once again performs check to skip evaluation
- MIP workflow once again updates StatusDB about the case status

## [12.2.0]

### Changed

- Merged methods cases_to_mip_analyze and cases_to_balsamic_analyze, now called cases_to_analyze for any pipeline.
- Made method cases_to_deliver pipeline aware
- Made method cases_to_store pipeline aware
- Made method cases_to_clean pipeline aware
- Added option to apply read count threshold for cases_to_analyze based on panel in ClinicalDB
- Updated MIP and BALSAMIC workflows to utilize the new methods
- Added tests for new methods in balsamic workflow
- Removed class FastqAPI. FastqAPI was only used by BALSAMIC, and contained one method. The method is now moved to FastqHandler class.

## [12.1.6]
### Fixed
- Create crunchy pending path outside batch script

## [12.1.5]
### Fixed
- support current orderform RML-1604:9 again

## [12.1.4]
### Changed
- Use long description from setup.py on PyPI

## [12.1.3]
### Fixed
- Use another parameter in build and publish

## [12.1.2]
### Fixed
- Syntax in github action build and publish workflow

## [12.1.2]
### Added
- Build and publish on pypi with github actions

## [12]
### Added
- Create a meta-API (BalsamicAnalysisAPI) to handle communication between balsamic and other cg applications. The API will handle the following:
   - Calling BalsamicAPI to execute balsamic commands
   - Query Lims and StatusDB to decide what arguments to pass to Balsamic
   - Read (new version of) deliverables report generated by Balsamic and store bundle in Housekeeper + StatusDB
- More info in https://github.com/Clinical-Genomics/cg/pull/687

### Changed
- Reduce number of options that can/should be passed to run the workflow. Most of the logic for determining the options will be handled by BalsamicAnalysisAPI.
- Every command now requires sample family name as argument.
- No longer support using sample_id to link files for sake of consistency.

## [11]
### Changed
- Removes all interactions with the beacon software

## [10.1.2]
### Fixed
- Fixed so that empty gzipped files are considered empty considering metadata

## [10.1.1]
### Added
- Adds a CHANGELOG.md
