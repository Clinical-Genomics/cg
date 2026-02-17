# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.0.0/)

<!-- Please add a new candidate release at the top after changing the latest one. Feel free to copy paste from the "squash and commit" box that gets generated when creating PRs

Try to use the following format:

__________ DO NOT TOUCH ___________


## [x.x.x]
### Added
### Changed
### Fixed


__________ DO NOT TOUCH ___________ -->

## [x.x.x]
### Added
### Changed
### Fixed
- README badge for CI - tests and coverage

## [22.26.0]
### Added
- Added median target coverage to mip:s pydantic model
- Added step to mips metric deliverables model

## [22.25.4]
### Fixed
- cg transfer pool: skip samples without pool name

## [22.25.3]
### Fixed
- Show warnings when priorities differ on a case in an order 

## [22.25.2]
### Fixed
- RML priority on pool-case

## [22.25.1]
### Fixed
- Database migration order

## [22.25.0]
### Added
- Support Orderform 1508:25, replaces Orderform 1541:6
- New Balsamic delivery types 
  - fastq-qc + analysis + cram
  - fastq-qc + analysis + cram + Scout

## [22.24.1]
### Fixed
- Handle empty values for synopsis in excel orders

## [22.23.2]
### Fixed
- Add proxy-protocol to dockerfile

## [22.23.1]
### Fixed
- Synopsis from old and new samples are combined

## [22.22.1]
### Added
- Added required ENV declarations in dockerfile
- pyyaml dependency required to run app in container

## [22.22.0]
### Added
- Fluffy samplesheet add control field

## [22.21.1]
### Fixed
- Balsamic delivery report exception text

## [22.21.0]
### Added
- Mark a NIPT/Fluffy sample as control

## [22.20.1]
### Fixed
- Accept synopsis both as list and as string in ordering json

## [22.20.0]
### Fixed
- Compatability of fluffy and new headers in dragen samplesheets

## [22.20.1]
### Added
- Case opencow and stillant to MIP validation cases

## [22.19.7]
### Added
- New fields, subject_id, phenotype_groups in clinical samples json orders for Scout 

## [22.19.5]
### Fixed
- improve avatar search

## [22.19.4]
### Fixed
- include dragen samplesheet in HK

## [22.19.3]
### Added
* Action to clean up workflow artifact cache

## [22.19.2]
### Fixed
- error in post demux process 

## [22.19.1]
### Fixed
- demultiplexed runs project checks

## [22.19.0]
### Added
- Novaseq Dragen Demultiplexing

## [22.18.0]
### Added
- Display number of samples in order ticket

## [22.17.2]
### Changed
- Raised sbatch memory parameter for demultiplexing

## [22.17.1]
### Fixed
- Delivery type also works for one type

## [22.17.0]
### Added
- Added support for multiple delivery flags for the command cg deliver analysis.

## [22.16.0]
### Added
- Function for downloading external data from caesar

## [22.15.0]
### Changed
- Methods in mutant config to AM doc number

## [22.14.0]
### Changed

- Removed balsamic bam and bam index files from cg deliver analysis command

## [22.13.0]

### Added

- MIP command to start after a given step

## [22.12.0]

### Added
- Add new model for qc_metrics
- Add new model for mip_analysis

### Changed
- Use new metrics deliverables format, which is already part of qc_metrics file
- Use new models when parsing mip analysis files

## [22.11.3]
### Fixed
- Show more errors from parsing orderforms 

## [22.11.2]
### Changed
- Update deployment instructions

## [22.11.1]
### Changed
- Updated bump2version action to v3
- Removed build container action (for time being) since we never use the containers

## [22.11.0]
### Fixed
- New families can be created without the --panel flag

## [22.10.3]
### Changed
- Increased flowcells ondisk cap


## [22.10.2]
### Fixed
- Fixed mean Q score added to cgstats by `cg demultiplex add <flowcell>` being off by a factor of 
100.

## [22.10.1]
### Fixed
- Integrate with bump2version-ci workflow

## [22.10.0]
### Fixed
- Changed how qos for rsync is handled


## [22.9.4]
### Fixed
- Cases removed from FOHM batch properly

## [22.9.3]
### Changed
- Remove KS validation cases from upload to GISAID/FOHM


## [22.9.2]
### Added
- Added UMI validation cases to skip spring compress

## [22.9.1]
### Fixed
- Send multiple emails properly
### Added
- Progress bar when uploading to FOHM

## [22.9.0]
### Added
- Samples that lack data during delivery is reported


## [22.8.6]
### Fixed
- Statina load use latest file

## [22.8.5]
### Fixed
- Sftp upload before sending email to FOHM

## [22.8.4]
### Fixed
- Tooltips for fohm upload functions


## [22.8.3]
### Added
- Data delivery export to LIMS 

## [22.8.2]
### Fixed
- Fail graceful if Avatar url lookup fails 

## [22.8.1]
### Changed
- Upload gisaid uses once again single fasta
- Upload gisaid uses pandas
- Upload gisaid uploads only qc pass files

## [22.8.0]
### Added
- Added support for FOHM batch upload



## [22.7.0]
### Added
- email functionality

### Changed
- gisaid upload command: gisaid cli log file will be saved in housekeeper with tag gisaid-log
- gisaid upload command: the log file will be appended to if the upload is run again for the same case.
- gisaid upload command: Accession numbers will be parsed from the log file 
- gisaid upload command: The completion file which already exists in housekeeper will be updated with accession numbers
- gisaid upload command: If files are missing or not all samples within the case were uploaded to gisiad, an email will be sent to logwatch.

## [22.6.1]
### Changed
- Add deepvariant for input file in upload to loqusDB

## [22.6.0]
### Added
- Added rsync processes into trailblazer
- Added cleanup of rsync directories

## [22.5.2]
### Fixed
- mip check if analysis is complete


## [22.5.1]
### Fixed
- Avatar name lookup problem 

## [22.5.0]
### Added
- Avatars for cases

## [22.4.1]
### Fixed
- Statina upload api call to raise error when server response is not ok

## [22.4.0]
### Fixed
- cg will no longer run rsync on the gpu nodes

## [22.3.1]
### Fixed
- Fixed statina load bug where missing headers prevented data from being read

## [22.3.0]
### Added
- Add a command to upload both to Statina and ftp 
- Adds a command to run the first command for all available cases

## [22.2.2]
### Changed
- Header in indexreport to versal letters

## [22.2.1]
### Added
- Add more files to the mip-rna delivery

## [22.2.0]
### Added
- Add cg clean fluffy_past_run_dirs command

## [22.1.3]
### Fixed
- Remove dependency to archived pypi colorclass

## [22.1.2]
### Changed
- Use slurm qos class and constants instead of hard coding priority options

## [22.1.1]
### Fixed
- Check for case name uniqueness before storing order to avoid half stored orders

## [22.1.0]
### Changed
- Rsync now run on slurm instead of the login node

## [22.0.1]
### Added
- Added two more cases to BALSAMIC's validation
### Changed
- Divided VALIDATION_CASES into their own workflow lists to find them easier 

## [22.0.0]
### Added
- Adds store and store-available commands that use Hermes
- Add pydantic models for mip config and mip sample info
- Add constants for getting housekeeper MIP analysis tags
  
### Changed
- Remove old MIP-DNA store command using cg internally
- Remove old unused fixtures

## [21.12.0]
### Added
- cli for upload of data to Statina

## [21.11.2]
### Fixed
- NIPT upload to sftp server

## [21.11.1]
### Changed
- Clarified the code for automatic decompression

## [21.11.0]
### Added
- Deliver, concatenate (if needed) and rsync in one command

## [21.10.0]
### Added
- Support for showing demultiplexing in CiGRID

## [21.9.3]
### Fixed
- bugfix

## [21.9.2]
### Fixed
- gisaid -fixing bug accidentally inserted in the previous pr.

## [21.9.1]
### Fixed
- gisaid get region and lab from sample udfs
- gisaid adjusting for new fasta consensus file in housekeeper
- gisaid removing failing tests

### Changed
### Fixed

## [21.12.0]
### Added
- Support for Orderform 1508:24 for Clinical Samples

## [21.9.0]
### Added
- Add Fluffy analysis results -> ftp upload functionality for cust002

## [21.8.3]
### Changed
- Set memory allocation to 95G when demultiplexing on slurm 

## [21.8.2]
### Changed
- Add batch-ref flag to command string for fluffy analyses

## [21.8.1]
### Changed
- Changed so that barcode report is written to the correct path

## [21.8.0]
### Added
- Command `cg demultplex report` to generate barcode report for demuxed flowcells
### Changed
- Automatically generate barcode report when post processing demultiplexed flowcell

## [21.7.2]
### Added
- Copy sample sheet to demuxed flowcell dir
- Create `copycomplete.txt` after demux post-processing is done

## [21.7.1]
### Fixed
- Fixed bug when checking if flowcell projects has been renamed

## [21.7.0]
### Added
- Added support for SARS-CoV-2 Orderform 2184.5 with fields for GISAID upload

## [21.6.9]
### Changed
- Check if versions are larger than known version when determining reverse complement in demultiplexing

## [21.6.8]
### Changed
- Validate that flowcell name is correct when demultiplexing

## [21.6.7]
### Fixed
- Fixed linking sample files from case bundle

## [21.6.6]
### Changed
- Check that logfile exists before doing demux post-processing

## [21.6.5]
### Changed
- Check if Unaligned dir exists before doing demux post-processing
### Fixed
- Fix bugs in create sample sheet all command

## [21.6.4]
### Fixed
- Fix so that delivery will not break if fastq bundle is missing when delivering results with ticket id

## [21.6.3]
### Fixed
- Fix bug in sqlalchemy models

## [21.6.2]
### Fixed
- If a boolean value is passed to `cg set sample -kv <key> <value>` a boolean is passed to the db

## [21.6.1]
### Fixed
- Fix bug in mip and balsamic crontab

## [21.6.0]
### Added
- Functionality to do demultiplexing post processing from CG

## [21.5.7]
### Fixed
- Set status to analyze when resolving decompression

## [21.5.6]
### Fixed
- Use only the first item from region and lab code values in mutant workflow.

## [21.5.5]
### Fixed
- Fix tag to deliver correct mutant result files to KS inbox

## [21.5.4]
### Fixed
- Block orders unintentionally reusing case names 

## [21.5.3]
### Fixed
- Set correct fluffy analysis finish path

## [21.5.2]
### Fixed
- Fixed content of fluffy samplesheet according to customer specification

## [21.5.1]
### Fixed
- By default fetch related flowcell information using `cg get sample <sample_id>`

## [21.5.0]
### Added
- User field for allowing order portal login
### Changed 
- Delivery/Invoicing/Primary Contacts are now relations from Customer to User in admin

## [21.4.4]
### Fixed
- Propagate all samples to microsalt, even those without reads

## [21.4.3]
### Fixed
- Display invoice contact on invoice

## [21.4.2]
### Fixed
- Remove default option for mip-dna priority

## [21.4.1]
### Changed
- Change how samples are fetched for cgstats select command
### Fixed
- Bug when fetching info with `cg demultiplex select`-command

## [21.4.0]
### Added
- A column in customer-group admin view in to show customers in the group

## [21.3.1]
### Fixed
- PDC backup destination server for 2500 flowcells

## [21.3.0]
### Changed
- Remove dependency `cgstats` from requirements.txt and move used functionality into CG

## [21.2.0]
### Added
- Functionality for the cgstats api in CG

## [21.1.0]
### Added
Select analyses to be uploaded to vogue based on analysis completed date (before or after a date, of between two dates)
Add uploaded to vogue date to analysis table
Only select potential analyses to upload that have not been uploaded

## [21.0.0]
### Changed
- Add support for balsamic 7.x.x
- Rework Balsamic server configurations

### Fixed
- Upload to scout now possible for all analysis types through cg upload scout

## [20.26.2]
### Added
- Added more DNA and RNA positive control cases to VALIDATION_CASES

## [20.26.1]
### Fixed
- Workflow linking also links undetermined files when

## [20.26.0]
### Changed
- Cases to analyze query checks if any samples in case are newer than latest analysis to start topups
- Microsalt config-case wont include samples that dont pass sequencing qc

## [20.25.0]
### Changed
- Changes that customer contact persons are referred to as emails instead of users. This removes the need to add each contact as a user in the system and it becomes easier to manage the user list

## [20.24.0]
### Added
- Show customers in user admin view

## [20.23.0]
### Added
- gisaid uppload support via cli
- gisaid API

## [20.22.0]
### Added
- Add command `cg get analysis` to view analysis information

## [20.21.1]
### Fixed
- Fix subprocess wildcard issue in deliver rsync

## [20.21.0]
### Added
- Added cg deliver rsync <ticket_id>

## [20.20.1]
### Fixed
- bug in cg clean scout-finished-cases

## [20.20.0]

## Added
- CLI command to deploy Loqusdb via shipping

## [20.19.5]

### Fixed
- fixed bug where CgError was raised with wrong arguments in AnalysisAPI

## [20.19.4]

### Fixed
- fixed bug that cgstats configs was saved as cg_stats in CGConfig

## [20.19.3]

### Fixed
- Update sequenced at timestamp of sample whenever sample has been sequenced and flowcell transferred

## [20.19.2]

### Fixed
- Bug when instantiating analysis api in upload

## [20.19.1]
### Fixed
- Bug when fetching the api in mip workflow cli base

## [20.19.0]

### Changed
- use pydantic to control CLI context 

## [20.18.0]
### Added
- Trailblazer support for mutant/sars-cov-2

## [20.17.5]
### Fixed
- Bugfix allowing orders of single samples from existing families

## [20.17.4]
### Added
- Added new covid prep method to lims constants

## [20.17.3]
### Fixed
- Adds support to use original sample lims id in downsampled cases (affects balsamic)

## [20.17.2]
### Fixed
- Fix duplicate Housekeeper session in scout upload


## [20.17.1]
### Changed
- Status of mutant cases is set to running before running analysis, and revoked if start fails. 
  This prevents users and cron jobs from starting the case which already started, given they check in statusDB first.

## [20.17.0]
### Added

- Deliver sarscov2 cli

## [20.16.0]
### Added

- Demultiplexing functionality to CG

## [20.15.1]
### Fixed
- cg to rename mutant fastq files directly

## [20.15.0]
### Added
- CLI methods for starting mutant

## [20.14.2]
### Added
- Add RNA validation cases to blacklist, which defines cases to not compress fastq files for

## [20.14.1]
### Fixed
- So that existing samples don't get added to lims again

## [20.14.0]
### Added
- Possibility to associate more than one customer to each user 

## [20.13.0]
### Changed
- Update orderform 2184 to latest version 4

## [20.12.1]
### Fixed
- Fix skip MIP-DNA (for MAF) for tumours with wgs applications for fastq delivery

## [20.12.0]
### Added
- Add support for fastq delivery

## [20.11.0]
### Added
- functionality to upload synopsis, cohort and phenotype information to scout

## [20.10.1]
### Fixed
- Mip start-available command

## [20.10.0]
### Added
- Panel command to mip-rna analysis workflow
- Add genome build 38 as default for mip-rna when exporting gene panels from Scout
- Add genome build 37 as default for mip-dna when exporting gene panels from Scout
- Add genome build 37 as default when exporting gene panels from Scout

### Changed
- Refactor start and start-available for mip

## [20.9.12]
### Changed
- Use pydantic models for handling lims samples


## [20.9.11]
### Fixed
- Fix bug that that prevented wgs fastq samples from being genotyped

## [20.9.10]
### Fixed
- Move synopsis and cohorts from sample to case in the database since that is how they are used 

## [20.9.9]
### Fixed
- Fixed bug in upload delivery report automation

## [20.9.8]
### Fixed
- Fixed context in upload vogue

## [20.9.7]
### Fixed
- Added missing pipeline option in database for SARS-CoV-2 on case in database

## [20.9.6]
### Fixed
- Use `coverage_qc_report` instead of `delivery_report` when uploading balsamic cases to scout

## [20.9.5]
### Fixed
- Balsamic crontab start-available auto-disables balsamic dry run

## [20.9.4]
### Fixed
- Fix bug that pending path was not created 

## [20.9.3]
### Fixed
- Bug in automation of delivery report upload

## [20.9.2]
### Fixed
- Bug when updating crunchy metadata files

## [20.9.1]
### Fixed
- Bug preventing MicroSALT to start automatically

## [20.9.0]
### Added
- SlurmAPI to handle all communication with slurm from cg

## [20.8.1]
### Changed
- Deletes unused files .gitlint, housekeeper, status, status_db

## [20.8.0]
### Added
- Support for creating delivery reports for analyses that are not the latest ones

## [20.7.0]
### Added
- DIAB and NBS-M to master list 

### Fixed
- Alphabetical order of master list

## [20.6.0]
### Changed
- Use cgmodels for crunchy metadata files

## [20.5.4]
### Added
- Change ending of lintjob from .py to .yml (accidentaly changed in previous pr)

## [20.5.3]
### Added
- Support for SARS-CoV-2 Orderform 2184:3

## [20.5.2]
### Changed
- Remove pipfile and pipfile.lock since they are not used

## [20.5.1]
### Changed
- Removes linting gh actions job

## [20.5.0]
### Added
- Add support for Microbial Orderform 1603:10
- Add support for Metagenome Orderform 1605:09

## [20.4.0]
### Added
- Support for SARS-CoV-2 Orderform 2184:1

## [20.3.3]

### Changed
- Set concentration and concentration sample to str in json orderform sample since this is expected in frontend

## [20.3.2]
### Fixed
- Fixed cases_to_store for microbial workflow. 
- Fixed process call for all workflows to not create a new process object

## [20.3.1]
### Fixed
- HousekeeperAPI to reuse db connection from context instead of creating new one for each call

## [20.3.0]
### Changed
- Refactored AnalysisAPI anf FastHandler classes into one class

## [20.2.1]
### Fixed
- Fixed json orderform special cases

## [20.2.0]
### Changed
- Use pydantic models to validate orderforms

## [20.1.4]
### Added
- delivery_report handling from BALSAMIC case import to Scout config export

## [20.1.3]
### Changed
- Genes are optional when exporting scout variants

## [20.1.2]
### Changed
- Refactored and removed code from cg.store.utils in backwards compatible way

## [20.1.1]
### Changed
- Updates issue template

## [20.1.0]
### Fixed
- Fix automatic decompression to also work for mixed cases

## [20.0.1]
### Changed
- Removed old unused scripts and scripts directory
- Moved crunchy query from store into CompressAPI


## [20.0.0]

### Changed
- cg workflow mip-rna link command to take case as positional arg

## [19.5.4]

### Changed
- Refactor ticket handling from orders API

## [19.5.3]
### Fixed
- Fix dry run flag when resolving decompression state

## [19.5.2]
### Fixed
- fix container name when publishing branch builds on dockerhub

## [19.5.1]

### Fixed
- changelog

## [19.5.0]

### Added
- alembic functionality
### Changed
- destination server PDC retrieval novaseq flowcells thalamus -> hasta
### Fixed
- flowcell status after PDC retrieval ondisk -> retrieved

## [19.4.0]

### Added
- Support for storing cohorts, phenotype_terms and synopsis from order json

## [19.3.2]
### Added
- Dockerhub build app container for release and pull requests
### Changed
- Changed CI actions that run on pull request on push to only run on pull request

## [19.3.1]
### Added
- Dockerfile declaration for running the cg app. Dockerfile should not be used for the cli toolkit

## [19.3.0]
### Added
- New options for balsamic report deliver to propagate delivery report data to Balsamic


## [19.2.0]
### Added
- Cases that decompression is started for will have the action set to "analyze"

## [19.1.1]

### Fixed
- Allow price update files for application-version import to have empty prices 


## [19.1.1]
### Added
- Cases that decompression is started for will have the action set to "analyze"

## [19.1.0]
### Added
- Cli command to deliver old balsamic analyses which were stored with old hk tags

## [19.0.0]

### Added
- Adds command to start decompression for spring compressed files if needed
### Changed
- Refactors MIP cli slightly to always expect a case id
- workflow start now called start-available
- Checking if flowcells are on disk moved to its own cli command

## [18.12.0]

### Added
- Add prep-category 'cov' for applications

## [18.11.4]

### Fixed
- Install package in gihub-jobs via pip==21.0.1

## [18.11.3]

### Fixed
- Upgraded insecure cryptography dependency 

## [18.11.2]

### Fixed
- Chromograph image tags back on track

## [18.12.1]

### Fixed
- Fix message in order ticket that says what type of project it is

## [18.11.1]

### Fixed
 - Fix so that variants gets uploaded to scout for balsamic samples
 - Fix so that upload breaks if balsamic case is WGS

## [18.11.0]
- New Fluffy workflow for preparing, starting and storing of analyses

## [18.10.2]

### Fixed
- FLUFFY now have a validation schema and can be submitted in the Order Portal again
- Samples of pools are now marked not to be invoiced, only the pool is invoiced

## [18.10.1]

### Added
- Allow existing trio-samples to be re-run as single samples 

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
