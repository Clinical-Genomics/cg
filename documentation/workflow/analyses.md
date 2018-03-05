# Analyses

Analyses are automatically started according to the "Families to analyze" queue. The family is then given an action of "running".

    @ rasta:~/servers/crontab/analysis-auto.sh
    $ cg analysis auto
    $ cg analysis -f FAMILY-ID

This process involves a set of steps that setup the environment to prepare for analysis start:

- [config](https://github.com/Clinical-Genomics/cg/blob/master/documentation/commands/analysis.md#1-config): a pedigree config is created in a "family" directory in the analysis root folder. Information is mainly fetched from _status_ with some exceptions like picking up capture kit version which is stored in LIMS.

      cg analysis config FAMILY-ID

- **link**: link and rename FASTQ files for each sample in the family. We rely on all FASTQ files to already be stored in _Housekeeper_ for each sample. Information to rename samples and link paried-end reads is fetched from the headers in the FASTQ-file itself.

      cg analysis link -f FAMILY-ID

- **panel**: generate a gene panel with relevant _clinical_ genes for the analysis. The latest version of the "OMIM-AUTO" panel is seeded with every analysis to avoid errors with very few variants in the output. Panels information is managed in _Scout_. For collaborating customers: cust002-4 we run a pre-defined set of panels for most cases.

      cg analysis panel FAMILY-ID

- **start**: just start the pipeline with existing config/FASTQs/panel. This can be useful if you need to make custom edits to the config that you want to run with.

      cg analysis start FAMILY-ID

The analysis is thereafter tracked in _Trailblazer_ until it's successfully completed. An analysis can fail and be restarted but when it eventually completes it is automatically picked up first by _Trailblazer_.

    @ rasta:~/servers/crontab/trailblazer-scan.sh
    $ trailblazer scan

Relevant files from all completed analyses are then stored in _Housekeeper_. An analysis record is also created in _status_ in this process. Finally, the action ("running") for the related family is reset.

    @ rasta:~/servers/crontab/store-completed.sh
    $ cg store completed
    $ cg store analysis [ANALYSIS-CONFIG-PATH]

The files to store are defined in the _Trailblazer_ API in _cg_.

Analysis output of completed runs should be cleaned up after two weeks if it's been stored in _Housekeeper_.

    cg clean auto

The command will promt you for confirmation before deleting any files.

## Failed runs

### `analysisrunstatus`

Failure in this step indicates a quality-related error. The next step is usually to make an assesment of the deviation. You can start by running:

    trailblazer check FAMILY-ID

This command will report sex determination and duplicates for all samples.

#### Saliva samples

#### Missing FASTQ files

Poor coverage can be caused by missing FASTQ files that weren't linked before analysis start. It could also be a result of certain sample origins, e.g. "saliva" where it's expected to see a higher number of duplicates and mapping to bacterial genome sequences. You can find out the origin of the sample in the "Source" sample UDF in LIMS.

