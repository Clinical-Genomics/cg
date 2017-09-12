# cg

`cg` stands for _Clinical Genomics_; a clinical sequencing platform under [SciLifeLab][scilife].

This is our main package for interacting with data and samples that flow through our pipeline. We rely on a set of specialized "apps" to deal with a lot of complexity like:

- [Trailblazer][trailblazer]: Python wrapper around MIP, a rare disease genomics pipeline
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

1. **Demux** | Samples are  picked up by the bioinformatics pipeline after sequencing. A demultiplexed flowcell will get added to `status` and FASTQ files for each sample will be sent to `housekeeper`. Meanwhile, reads count are updated which moves the samples to the next step.

1. **Analysis** | Samples are always analyzed as "families". If a family of samples all have been sequenced, they show up in the **analysis queue**. Analyses are automatically started by a crontab script.

    Families with elevated priority (priority/express) will be started first with the rest following in reverse chronological order.

    Starting a run will do four things:

    1. Generate a pedigree config for the analysis pipeline
    1. Link FASTQ files for each related sample and rename to follow the pipeline conventions
    1. Generate a gene panel file according to the order
    1. Start the pipeline and set the priority flag to high if required

    A crontab is monitoring the progress of started runs. You can follow the status in [Trailblazer][trailblazer-ui].

1. **Store** | Completed analyses can be accessed through `trailblazer` and are automatically "stored". This process updates `status` and links files to the family in `housekeeper`.

    Some files are marked as essential and will be subsequently backed up. The rest of the files are removed after 3 months.

1. **Upload** | Results from completed analyses are uploaded to a range of different tools:

    - [Chanjo][chanjo]: coverage metrics
    - [Genotype][genotype]: genotypes for detecting sample mix-ups
    - LoqusDB: local observation counts for variants
    - [Scout][scout]: variant interpretation platform

    We also gather statistics from analysis (post-alignment) which we use to generate a delivery report, however, this is still under development.

1. **Delivery** | Delivery happens on two levels:

    - **Sample**: FASTQ-files are always delivered for every order. The default is delivery to the delivery server. We also support upload to UPPMAX and other generic servers for some collaborators. After delivery, `status` is updated with a final sample progress date.

    - **Family/Analysis**: some collaborators have opted into the Scout platform for delivery of annotated and ranked variants. These families are analyzed and uploaded which essentially corresponds to the "delivery" for such orders. We do, however, perform various quality checks before we finally answer out the results.

1. **Archive**: [@ingkebil][ingkebil]

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

[portal]: https://clinical-db.scilifelab.se:7071/
[trailblazer]: https://github.com/Clinical-Genomics/trailblazer
[trailblazer-ui]: https://apps.clinicalgenomics.se/trailblazer-ui
[housekeeper]: https://github.com/Clinical-Genomics/housekeeper
[genotype]: https://github.com/Clinical-Genomics/genotype
[chanjo]: https://github.com/robinandeer/chanjo
[scout]: https://github.com/Clinical-Genomics/scout
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
