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
