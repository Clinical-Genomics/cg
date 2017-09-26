# cg

`cg` stands for _Clinical Genomics_; a clinical sequencing platform under [SciLifeLab][scilife].

This is our main package for interacting with data and samples that flow through our pipeline. We rely on a set of specialized "apps" to deal with a lot of complexity like:

- [Trailblazer][trailblazer]: Python wrapper around [MIP][mip], a rare disease genomics pipeline
- [Housekeeper][housekeeper]: storage, retrieval, and archive of files
- [Genotype][genotype]: managing genotypes for detecting sample mix-ups

In this context, `cg` provides the interface between these tools to facilitate automation and other necessary cross-talk. It also exposes some APIs:

- HTTP REST for powering the web portal: [clinicalgenomics.se][portal]
- CLI for interactions on the command line

## Team

- [@ingkebil][ingkebil]: bioinformatics manager | 🇧🇪
- [@robinandeer][robinandeer]: lead developer, designer | 🇸🇪
- [@Dilea][Dilea]: bioinformatician, LIMS developer | 🇸🇪
- [@b4ckm4n][b4ckm4n]: bioinformatician | 🇸🇪
- [@emmser][emmser]: bioinformatician | 🇸🇪 👶
- [@northwestwitch][northwestwitch]: bioinformatician, variant sharing expert 🇮🇹
- [@mayabrandi][mayabrandi]: bioinformatician, lead LIMS developer | 🇸🇪 👶
- [@moonso][moonso]: bioinformatician, Scout developer | 🇸🇪
- [@henrikstranneheim][henrikstranneheim]: bioinformatician, MIP developer | 🇸🇪

## Work flow

![Work flow overview](artwork/overview.png)

This is a schematic overview of how data flows between different tools. Generally things start in the top left corner:

1. **Order** | New samples are submitted by logging into the [portal][portal] and either uploading an "orderform" or supplying the information directly.

    Information is parsed and uploaded both to LIMS and to the status database. These samples now end up in the **incoming queue**.

    Samples are marked with a date of reception in LIMS. A crontab syncronizes this information over to the status database and moves the samples along.

1. **Lab** | Samples are prepped on and monitored in LIMS. This is true for all lab related activities  until sequencing. Until fully sequenced (as defined by the application tag), samples stay in the **sequencing queue**.

1. **Demux** | Samples are  picked up by the bioinformatics pipeline after sequencing. A demultiplexed flowcell will get added to `status` and FASTQ files for each sample will be sent to `housekeeper`. Meanwhile, read count are updated which moves the samples to the next step.

    You can (re-)perform the transfer at any time, you just need the flowcell id:

    ```bash
    cg transfer flowcell [flowcell]
    ```

    > TODO: reads are only counted for samples that pass the **Q30 threshold**. You can override this check by using the `--force` flag.

1. **Analysis** | Samples are always analyzed as "families". If all samples in a family have been sequenced, it show up in the **analysis queue**. Analyses are automatically started by a crontab script.

    Families with elevated priority (priority/express) will be started first with the rest following in reverse chronological order.

    Starting a run will do four things:

    1. Generate a pedigree config for the analysis pipeline (`cg analysis config FAMILY`)
    1. Link FASTQ files for each related sample and rename to follow the pipeline conventions (`cg analysis link FAMILY`)
    1. Generate a gene panel file according to the order (`cg analysis panel FAMILY`)
    1. Start the pipeline and set the priority flag to high if required (`cg analysis start FAMILY`)

    A crontab is monitoring the progress of started runs. You can follow the status in [Trailblazer][trailblazer-ui].

    You can start an anlysis in a couple different ways:

    1. set the action property of the family to "analyze"
    1. run the command: `cg analysis -f [family]`

1. **Store** | Completed analyses can be accessed through `trailblazer` and are automatically "stored". This process updates `status` and links files to the family in `housekeeper`.

    Some files are marked as essential and will be subsequently backed up. The rest of the files are removed after 3 months.

    If you are in a hurry, you can store a completed analysis manually by running:

    ```bash
    cg store analysis FAMILY
    # or store all the recently completed runs
    cg store completed
    ```

1. **Upload** | Results from completed analyses are uploaded to a range of different tools:

    - [Chanjo][chanjo]: coverage metrics
    - [Genotype][genotype]: genotypes for detecting sample mix-ups
    - LoqusDB: local observation counts for variants
    - [Scout][scout]: variant interpretation platform

    We also gather statistics from analysis (post-alignment) which we use to generate a delivery report, however, this is still under development.

1. **Delivery** | Delivery happens on two levels:

    - **Sample**: FASTQ-files are always delivered for every order. The default is delivery to the delivery server. We also support upload to UPPMAX and other generic servers for some collaborators. After delivery, `status` is updated with a final sample progress date.

    - **Family/Analysis**: some collaborators have opted into the Scout platform for delivery of annotated and ranked variants. These families are analyzed and uploaded which essentially corresponds to the "delivery" for such orders. We do, however, perform various quality checks before we finally answer out the results.

1. **Archive** | Essential result files and raw data coming from the sequencers will sent off-site for slow storage.

## Responsibilities

Genomics platforms produce vasts amount of data and we deal with 1000s of samples every year. This leads to a rather complex interaction of tools and databases to handle this throughput. We also strive to automate as much of the processes as possible.

We therefore need to share responsibilities and monitoring between members of our team.

### Processes

- **Order**: [@robinandeer][robinandeer]
- **Demux**: [@ingkebil][ingkebil]
- **Analysis**: [@Dilea][Dilea]
- **Upload**: [@robinandeer][robinandeer]
- **Delivery**: [@b4ckm4n][b4ckm4n]
- **Archive**: [@ingkebil][ingkebil]

### Tools

- **LIMS**: [@Dilea][Dilea]
- **LoqusDB**: [@moonso][moonso]
- **Scout**: [@robinandeer][robinandeer] + [@moonso][moonso]
- **MIP**: [@henrikstranneheim][henrikstranneheim]

### Databases

- **MySQL**, host: clinical-db.scilifelab.se, [@ingkebil][ingkebil]

  - `/cg` - status
  - `/chanjo4` - Chanjo, coverage

- **MySQL**, host: clinical-genomics.cyxfn5r4quzp.eu-central-1.rds.amazonaws.com, [@robinandeer][robinandeer]

  - `/csdb` - CGStats, demux
  - `/housekeeper2` - Housekeeper, file management
  - `/mwgs` - Microbial pipeline, statistics
  - `/taboo` - Genotype
  - `/trailblazer` - Trailblazer, MIP analysis monitoring

- **MongoDB**, host: clinical-db.scilifelab.se, [@robinandeer][robinandeer]

  - `/scout` - Scout, variant visualizer
  - `/loqusdb` - LoqusDB, variant observation counts

## Server

The REST API server handles a number of actions. It's written in [Flask][flask] and exposes an admin interface for quickly editing information in the backend MySQL database.

The API is protected by JSON Web Tokens generated by Google OAuth. It authorizes access using the user table in the internal database. The admin interface is served under a hidden route but the plan is to move it to Google OAuth as well.

### Order endpoint

The `/order/<type>` endpoint accepts orders for new samples. If you supply a JSON document on the expected format, a new order is open in `status` and LIMS.

## This package

This package is a little special. Essentially it should include all the "Clinical"-specific code that has to be integrated across multiple tools such as LIMS, Trailblazer, Scout etc. However, we still aim to structure it in such a way as to make maintainance as smooth as possible!

### `apps`

This part of the package contains connectors to the various tools that we integrate with. An app interface can be a wrapper for an external tool like Trailblazer (`tb`) or be implemented completely in `cg` like `lims`. It's very important that the code stays confined to each individual tool. The Housekeeper connector _cannot_ directly talk to Trailblazer for example - such communication has to go through a `meta` module.

We also try to group all app-related imports and functionality in these interfaces. You shouldn't import e.g. a function from Scout from any other place than its app interface. This way, it's easier to overview if an update to an external package will affect the rest of the system.

#### coverage

Interface to [Chanjo][chanjo]. It's used to load coverage information from Sambamba output.

#### invoice

Internal app for working with invoices of groups of samples or pools.

#### lims

Internal app for interfacing with the Clarity LIMS API. We use the `genologics` Python API as far as possible. Some actions are not supported, however, and then we fall back to using the official XML-based REST API directly.

We convert all the info that we get from LIMS/`genologics` to dictionaries before passing it along to other tools. We don't pass around objects that have some implicit connection to update things in LIMS - such actions needs to go through the `lims` app interface _explicitly_.

#### tb

Interface to Trailblazer.

- One responsibility is to define the set of files from MIP to store (in Housekeeper)
- Also used to interact with the pipeline for starting it

#### gt

Interface to Genotype. For uploading results from the pipeline about genotypes to compare and validate that we are clear of sample mix-ups.

#### hk

Interface to Housekeeper. For storing files from analysis runs and FASTQ files from demultiplexing.

#### loqus

Interface to LoqusDB. For loading observation counts from the analysis output.

#### osticket

Internal app for opening tickets in SupportSystems. We use this mainly to link a ticket with the opening of an order for new samples/analyses.

#### scoutapi

Interface to Scout. For uploading analysis results to Scout. It's also used to access the generation of gene panels files used in the analysis pipeline.

#### stats

Interface to CGStats. Used to handle things related to flowcells:

- this is where we find out how many reads a sample have been sequened
- getting paths to FASTQ files for samples/flowcells

### `cli`

The command line code is written in the [Click][click] framework.

#### add

This set of commands let's you quite easily _add things to the status database_. For example when a new customer is signed you could run:

```bash
cg add customer cust101 "Massachusetts Institute of Technology"
```

You can also accomplish simliar tasks through the admin interface of the REST server.

#### analysis

The MIP pipeline is accessed through Trailblazer but `cg` provides additional conventions and hooks into the status database that makes managing analyses simpler.

You can start the analysis of a single family "raredragon" by just running:

```bash
cg analysis --family raredragon
```

This command will create the MIP config in the correct location, link and rename FASTQ files from Housekeeper, and write an aggregated gene panel file. Then it will start the pipeline. All these 4 actions can be issued individually as well:

```bash
cg analysis [config|link|panel|start] raredragon
```

The final command is intended to run in a crontab and will continously check for families where all samples have been sequenced and start them automatically.

```bash
cg analysis auto
```

#### status

The main interface for getting an overview of data in the system is provided through the [web interface][cgweb], however, it's possible to use the same database APIs to get an idea of the status of things from the command line.

To get a list of families that are waiting in the analysis queue e.g. you can run:

```bash
cg status analysis
```

To get a general overview of samples or a sample in particular:

```bash
cg status samples ADM4565A1
ADM4565A1 (17101-1-1A) [SEQUENCED: 2017-09-02]
```

#### store

This group of commands facilitate the Housekeeper integration. For example, when an analysis finishes and you want to store important files and update the status database accordingly, you run:

```bash
cg store analysis /path/to/families/raredragon/analysis/raredragon_config.yaml
```

... or just wait for the crontab process to pick up the analysis automatically:

```bash
cg store completed
```

#### transfer

Some information will always exist across multiple database and requires some continous syncing to keep up-to-date. This is the case for information primarily entered through LIMS. To automatically fill-in the date of sample reception for all samples that are waiting in the queue:

```bash
cg transfer lims --status received
```

And similarly for filling in the delivery date:

```bash
cg transfer lims --status delivered
```

Another common task is to transfer data and FASTQ files from the demux/cgstats interface when a demultiplexing task completes. This is as easy as determining the flowcell of interest and running:

```bash
cg transfer flowcell HGF2KBCXX
```

The command will update the _total_ read counts of each sample and check against the application for the sample if it has been fully sequenced. It will also make sure to link the related FASTQ files to Housekeeper. You can run the command over and over - only additional information will be updated.

#### upload

Much like the group of analysis subcommands you can perform an upload of analysis results (stored in Housekeeper) all at once by running:

```bash
cg upload --family raredragon
```

All analyses that are marked as completed will be uploaded this way automatically:

```bash
cg upload auto
```

You can of course specify which upload you want to do yourself as well:

```bash
cg upload [coverage|genotypes|observations|scout] raredragon
```

### `meta`

This is the interfaces that bridge various apps. An example would be the "orders" module. When placing orders we need to coordinate information/actions between the apps: `lims`, `status`, and `osticket`. It also provides some additional functionality such as setting up the basis for the orders API and which fields are required for different order types.

#### orders

Includes: `lims`, `status`, `osticket`

The API exposes a single endpoint for submitting a batch of new samples/external samples for analysis. It handles a mix of updates to existing samples with entierly new ones. The API is designed to work well in a REST API context.

The interface supports:

- samples for sequencing + analysis (**scout**)
- samples for sequencing only (**fastq**)
- sequencing of ready-made libraries (**rml**)
- analysis of externally sequenced samples (**external**)

It opens a ticket using the `osticket` API for each order which it links with the ticket number. It stores information in both LIMS and `status` for samples and pools linked by LIMS id. It stores only a minimum of information about each sample in LIMS. Most of the critial information is stored in `status` and this is also the primary place to go if we need to update e.g. application tag for a sample.

#### transfer

This interface has a few related roles:

##### flowcell

Includes: `stats`, `hk`, `status`

The API accepts the name of a flowcell which will be looked up in `stats`. For all samples on the flowcell it will:

1. check if the quality (Q30) is good enough to include the sequencing results.
1. update the number of reads that the sample has been sequenced _overall_ and match this with the requirement given by the application.
1. accordingly, the interface will look up FASTQ files and store them using `hk`.
1. if a sample has sufficent number of reads, the `sequenced_at` date will be filled in (`status`) according to the sequencing date of the most recent flowcell.

##### lims

Includes: `status`, `lims`

Some info if primarily stored in LIMS and needs to be syncronized over to `status`. This is the case for both the date when a samples was received and when it was finally delivered. This interface is intended to run continously as part of a crontab job.

#### upload

##### coverage

Includes: `status`, `hk`, `coverage`

The API will fetch information about an analysis like name and id of the family and related samples from `status`. It will get the Sambamba output from `hk` and use the `coverage` app interface to upload the data to Chanjo for each individual sample.

##### gt

Includes: `status`, `hk`, `tb`, `gt`

Given an analysis, the API will fetch information about the family. It will fetch the gBCF + qcmetrics files from `hk`. It will parse the qcmetrics file using `tb` to find out the predicted sex of each sample. It will then upload the results to Genotype. Subsequent upload of the same samples will overwrite existing information while logging the event.

##### observations

Includes: `status`, `hk`, `loqus`

Given an analysis record, it will fetch required files from `hk` and upload the variants to the observation cound database using `loqus`. This only works for families with at least one affected individual.

##### scoutapi

Includes: `status`, `hk`, `scoutapi`

Given the analysis record it will generate a Scout config file using information from `status`. It will use the "meta/analysis" API to convert the default panels for the family to the corresponding set of panels used to run the analysis. It will fetch all related VCF files and others from `hk`. Finally it will use the config to upload the resuls to Scout. The `scoutapi` interface will figure out if there's an existing analysis that needs to be replaced.

#### analysis

Includes: `status`, `tb`, `hk`, `scoutapi`, `lims`

Starting an analysis requires complex interactions of many individual tools:

- the config/pedigree is almost entirely generated from info in `status`
- the only exception is the bait kit for targetted sequencing samples which is fetched using `lims`
- the gene panel file that determines the "clinical" variants is generated from the panels assigned to the family in `status` by using `scoutapi`
- the FASTQ files are fetched for each sample in the family from `hk` and renamed and placed in the correct location using `tb`
- the analysis is finally started using `tb`

We need to keep track of running analyses so we don't start the same family twice. This status is maintained by the "action" field in `status` which can be used to control when to start runs:

- **[EMPTY]**: the empty state will trigger an automatic start of the analysis when all related samples have been sequenced AND no previous analysis of the family has occured
- **analyze**: to re-run an analysis of a family you just need to set the field to "analyze" and it will start regardless if a previous analysis has completed
- **running**: this state will be maintained after a successful start of a family until it has completed. If the analysis fails you need to manually make sure to restart it OR set the field to "analyze".
- **hold**: this state will make sure that the family is excluded from any automated starts, however, it will not affect/warn when you start an analysis of the family manually

You update the status via the admin interface of the server.

#### invoice

Includes: `status`, `lims`

The creation of an invoice is initiated in LIMS. You then use the process id to parse out which samples should be part of the invoice. This process is setup to be run when a button is clicked in LIMS but can be run externally from any server with access to LIMS.

The invoice itself will be stored in an intermediate state in `status` while links will be created in LIMS to be able to keep track of which samples was part of which invoice.

### `server`

The REST interface and database admin interface are implemented in [Flask][flask]. Authentication for the REST interface is handled using Google OAuth backed JWT tokens. The admin interface is authenticated using a secret key which corresponds to the route you need to access to get to it.

### `store`

This really is the `status` app more or less. It's the interface to the central database that keeps track of samples and it which state they are currently in. All records that enters the database go through this API. Simple updates to properies on records are handled directly on the model instances followed by a manual commit.

### Misc.

There's one file for storing all constants like how priority levels are translated between the database representation and the human readable equivalent.

Another module `/exc.py` contains the custom Exception classes that are used across the package.


[portal]: https://clinical-db.scilifelab.se:7071/
[trailblazer]: https://github.com/Clinical-Genomics/trailblazer
[trailblazer-ui]: https://apps.clinicalgenomics.se/trailblazer-ui
[housekeeper]: https://github.com/Clinical-Genomics/housekeeper
[genotype]: https://github.com/Clinical-Genomics/genotype
[chanjo]: https://github.com/robinandeer/chanjo
[scout]: https://github.com/Clinical-Genomics/scout
[mip]: https://github.com/Clinical-Genomics/mip
[scilife]: https://www.scilifelab.se/
[flask]: http://flask.pocoo.org/
[ingkebil]: https://github.com/ingkebil
[robinandeer]: https://github.com/robinandeer
[Dilea]: https://github.com/Dilea
[b4ckm4n]: https://github.com/b4ckm4n
[moonso]: https://github.com/moonso
[henrikstranneheim]: https://github.com/henrikstranneheim
[emmser]: https://github.com/emmser
[northwestwitch]: https://github.com/northwestwitch
[mayabrandi]: https://github.com/mayabrandi
[click]: http://click.pocoo.org/5/
[cgweb]: https://github.com/Clinical-Genomics/cgweb
