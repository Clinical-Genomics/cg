# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.0.0/)

Please add a new candidate release at the top after changing the latest one. Feel free to copy paste from the "squash and commit" box that gets generated when creating PRs

Try to use the following format:

## [x.x.x]

### Added

### Changed
- Update Scout config output for images from chromograph
### Fixed


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
