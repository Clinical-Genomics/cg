# Contributing to CG

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

This is a guide for contributing to the CG package. Please check here first if you want to [set up an environment and develop](#local-development), [open and issue](#reporting-bugs), [suggest an enhancement](#suggesting-enhancements), [open a pull request](#pull-requests) etc.

#### Table Of Contents

[Code of Conduct](#code-of-conduct)

[Branch Model](#branch-model)

[How Can I Contribute?](#how-can-i-contribute)
  * [Reporting Bugs](#reporting-bugs)
  * [Suggesting Enhancements](#suggesting-enhancements)
  * [Your First Code Contribution](#your-first-code-contribution)
  * [Pull Requests](#pull-requests)

[Styleguides](#styleguides)
  * [Git Commit Messages](#git-commit-messages)
  * [Python style guide](#python-styleguide)
  * [Documentation Styleguide](#documentation-styleguide)

[CG Design decisions](#design-decisions)
  * [apps](#apps)
  * [CLI](#cli)
  * [meta](#meta)
  * [server](#sever)
  * [store](#store)




## Code of Conduct

Communicating around code can be a sensitive thing so please do your best to keep a positive tone. Remember that people are putting significant amount of work behind a PR or a review, stay humble :star:


## Branch Model

CG is using github flow branching model as described in our [development manual][development-branch-model].


## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report to CG. Following these guidelines helps other developers and contributors understand your report :pencil:, reproduce the behavior :computer: :computer:, and find related issues and reports :mag_right:

Before creating bug reports, please try to search the issues (opened and closed) if the problem has been described before, there might be no reason to create one. When creating a bug report, please [include as many details as possible](#how-do-i-submit-a-good-bug-report).

> **Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one.


#### How Do I Submit A (Good) Bug Report?

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/).

Explain the problem and include additional details to help maintainers reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible. For example, start by explaining where CG was run and how it was used, i.e. which command exactly you used in the terminal.
* **Provide specific examples to demonstrate the steps**. Include links to files or case IDs, or copy/pasteable snippets, which you use in those examples. If you're providing snippets in the issue, use [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**

Provide more context by answering these questions:

* **Can you reproduce the problem**?
* **Did the problem start happening recently** (e.g. after updating to a new version of CG) or was this always a problem?
* If the problem started happening recently, **can you reproduce the problem in an older version of CG?** What's the most recent version in which the problem doesn't happen? You can test and run older versions of CG in the stage environments by using the `update-cg-stage.sh` script.

Include details about your configuration and environment:

* **Which version of CG are you using?** You can get the exact version by running `cg --version` in your terminal.
* **What's the name of the environment you're using**?

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for CG, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion :pencil: and find related suggestions :mag_right:


#### How Do I Submit A (Good) Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://guides.github.com/features/issues/). To suggest an enhancement create an issue on that repository and provide the following information:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets which you use in those examples, as [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful**


#### Local Development

**NEVER USE PREINSTALLED PYTHON**

First of all, make sure that you are managing your python versions that are used on your machine, [never use the OS native python](https://docs.python-guide.org/starting/installation/). Suggested ways to handle python version are either through [homebrew](https://brew.sh/#install)(OSX), [pyenv](https://github.com/pyenv/pyenv) or [conda](https://docs.anaconda.com/anaconda/install/).


On our servers where the production and stage versions of CG are run the packages are maintained by using conda environments. For local development it is suggested to follow the [python packaging guidelines](https://packaging.python.org/tutorials/managing-dependencies/) where it is suggested to manage your local python environment with [pipenv](https://pipenv.pypa.io/en/latest/). CG has a Pipfile.lock file which will ensure that the installation will work if the environment is set up in the correct way. To use a **combination of conda and pipenv** make sure that you point to the conda installation of python when creating your pipenv virtual environment (`pipenv --python=$(conda run which python) --site-packages`) more about that [here](https://pipenv.pypa.io/en/latest/advanced/#pipenv-and-other-python-distributions) and in [this](https://stackoverflow.com/questions/50546339/pipenv-with-conda) stack overflow thread. (It is not necessary to use conda on for local development)


When pipenv is installed just create a new environment and run `pipenv install`

### Pull Requests

The process described here has several goals:

- Maintain CG's quality
- Engage the developers in working toward the best possible CG
- Enable a sustainable system for CG's maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow all instructions in [the template](.github/PULL_REQUEST_TEMPLATE.md)
1. Follow the [styleguides](#styleguides)
1. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing <details><summary>What if the status checks are failing?</summary>If a status check is failing, and you believe that the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you.</details>
1. Update CHANGELOG.md with relevant information


While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python styleguide

We use black to format all files, this is done automatically with each push on GitHub so don't forget to update your local branch with `git pull` after pushing to the origin. More details are described in the general [development manual][development-guidelines].

[development-guidelines]: http://www.clinicalgenomics.se/development/python/conventions/
[development-branch-model]: http://www.clinicalgenomics.se/development/dev/githubflow/

## Design decisions

This package is a little special. Essentially it should include all the "Clinical"-specific code that has to be integrated across multiple tools such as LIMS, Trailblazer, Scout etc. However, we still aim to structure it in such a way as to make maintainance as smooth as possible!

### Apps

This part of the package contains connectors to the various tools that we integrate with. An app interface can be a wrapper for an external tool like Trailblazer (`tb`) or be implemented completely in `cg` like `lims`. It's very important that the code stays confined to each individual tool. The Housekeeper connector _cannot_ directly talk to Trailblazer for example - such communication has to go through a `meta` module.

We also try to group all app-related imports and functionality in these interfaces. You shouldn't import e.g. a function from Scout from any other place than its app interface. This way, it's easier to overview if an update to an external package will affect the rest of the system.

#### Coverage

Interface to [Chanjo][chanjo]. It's used to load coverage information from Sambamba output.

#### Invoice

Internal app for working with invoices of groups of samples or pools.

#### Lims

Internal app for interfacing with the Clarity LIMS API. We use the `genologics` Python API as much as possible. Some actions are not supported, however, and then we fall back to using the official XML-based REST API directly.

We convert all the info that we get from LIMS/`genologics` to dictionaries before passing it along to other tools. We don't pass around objects that have some implicit connection to update things in LIMS - such actions needs to go through the `lims` app interface _explicitly_.

#### Trailblazer (tb)

Interface to Trailblazer.

- Monitor analysis pipeline status

#### Genotype (gt)

Interface to Genotype. For uploading results from the pipeline about genotypes to compare and validate that we are clear of sample mix-ups.

#### Housekeeper (hk)

Interface to Housekeeper. For storing files from analysis runs and FASTQ files from demultiplexing.

#### Loqus

Interface to LoqusDB. For loading observation counts from the analysis output.

#### Osticket

Internal app for opening tickets in SupportSystems. We use this mainly to link a ticket with the opening of an order for new samples/analyses.

#### Scout (scoutapi)

Interface to Scout. For uploading analysis results to Scout. It's also used to access the generation of gene panels files used in the analysis pipeline.

#### CGStats (stats)

Interface to CGStats. Used to handle things related to flowcells:

- this is where we find out how many reads a sample have been sequened
- getting paths to FASTQ files for samples/flowcells

### Cli

The command line code is written in the [Click][click] framework.

#### Add

This set of commands let's you quite easily _add things to the status database_. For example when a new customer is signed you could run:

```bash
cg add customer cust101 "Massachusetts Institute of Technology"
```

You can also accomplish simliar tasks through the admin interface of the REST server.

#### Transfer

##### Lims

Includes: `status`, `lims`

Some info if primarily stored in LIMS and needs to be syncronized over to `status`. This is the case for both the date when a samples was received and when it was finally delivered. This interface is intended to run continuously as part of a crontab job.

```bash
cg transfer lims --status received
```

And similarly for filling in the delivery date:


```bash
cg transfer lims --status delivered
```

##### Flowcell

Includes: `stats`, `hk`, `status`

The API accepts the name of a flowcell which will be looked up in `stats`. For all samples on the flowcell it will:

1. Check if the quality (Q30) is good enough to include the sequencing results
1. update the number of reads that the sample has been sequenced _overall_ and match this with the requirement given by the application.
1. accordingly, the interface will look up FASTQ files and store them using `hk`.
1. if a sample has sufficient number of reads, the `sequenced_at` date will be filled in (`status`) according to the sequencing date of the most recent flowcell.

Another common task is to transfer data and FASTQ files from the demux/cgstats interface when a demultiplexing task completes. This is as easy as determining the flowcell of interest and running:

```bash
cg transfer flowcell HGF2KBCXX
```

The command will update the _total_ read counts of each sample and check against the application for the sample if it has been fully sequenced. It will also make sure to link the related FASTQ files to Housekeeper. You can run the command over and over - only additional information will be updated.


### Meta

This is the interface that bridge various apps. An example is the "orders" module. When placing orders we need to coordinate information/actions between the apps: `lims`, `status`, and `osticket`. It also provides some additional functionality such as setting up the basis for the orders API and which fields are required for different order types.

#### Orders

Includes: `lims`, `status`, `osticket`

The API exposes a single endpoint for submitting a batch of new samples/external samples for analysis. It handles a mix of updates to existing samples with entierly new ones. The API is designed to work well in a REST API context.

The interface supports:

- samples for sequencing + analysis (**scout**)
- samples for sequencing only (**fastq**)
- sequencing of ready-made libraries (**rml**)
- analysis of externally sequenced samples (**external**)
- sequencing and analysis of microbial whole genomes (**microbial**)

It opens a ticket using the `osticket` API for each order which it links with the ticket number. It stores information in both LIMS and `status` for samples and pools linked by LIMS id. It stores only a minimum of information about each sample in LIMS. Most of the critial information is stored in `status` and this is also the primary place to go if we need to update e.g. application tag for a sample.


#### Upload

##### Coverage

Includes: `status`, `hk`, `coverage`

The API will fetch information about an analysis like name and family ID and related samples from `status`. It will get the Sambamba output from `hk` and use the `coverage` app interface to upload the data to Chanjo for each individual sample.

##### Gt

Includes: `status`, `hk`, `tb`, `gt`

Given an analysis, the API will fetch information about the family. It will fetch the gBCF + qcmetrics files from `hk`. It will parse the qcmetrics file using `tb` to find out the predicted sex of each sample. It will then upload the results to Genotype. Subsequent upload of the same samples will overwrite existing information while logging the event.

##### Observations

Includes: `status`, `hk`, `loqus`

Given an analysis record, it will fetch required files from `hk` and upload the variants to the observation cound database using `loqus`. This only works for families with at least one affected individual.

##### Scoutapi

Includes: `status`, `hk`, `scoutapi`

Given the analysis record it will generate a Scout config file using information from `status`. It will use the "meta/analysis" API to convert the default panels for the family to the corresponding set of panels used to run the analysis. It will fetch all related VCF files and others from `hk`. Finally it will use the config to upload the resuls to Scout. The `scoutapi` interface will figure out if there's an existing analysis that needs to be replaced.

#### Invoice

Includes: `status`, `lims`

The creation of an invoice is initiated in LIMS. You then use the process ID to parse out which samples should be part of the invoice. This process is setup to be run when a button is clicked in LIMS but can be run externally from any server with access to LIMS.

The invoice itself will be stored in an intermediate state in `status` while links will be created in LIMS to be able to keep track of which samples was part of which invoice.

### Server

The REST API server handles a number of actions. It's written in [Flask][flask] and exposes an admin interface for quickly editing information in the backend MySQL database. The admin interface is served under a hidden route but the plan is to move it to Google OAuth.

The API is protected by JSON Web Tokens generated by Google OAuth. It authorizes access using the user table in the database.

#### Order endpoint

The `/order/<type>` endpoint accepts orders for new samples. If you supply a JSON document on the expected format, a new order is opened in `status` and LIMS.

### Store

This really is the `status` app more or less. It's the interface to the central database that keeps track of samples and it which state they are currently in. All records that enters the database go through this API. Simple updates to properies on records are handled directly on the model instances followed by a manual commit.

### Misc.

There's one file for storing all constants like how priority levels are translated between the database representation and the human readable equivalent.

Another module `/exc.py` contains the custom Exception classes that are used across the package.

Some unit tests make use of [snapshottest][snapshottest]. To update existing snapshots run `pytest --snapshot-update`

[trailblazer]: https://github.com/Clinical-Genomics/trailblazer
[trailblazer-ui]: https://trailblazer.scilifelab.se/
[housekeeper]: https://github.com/Clinical-Genomics/housekeeper
[genotype]: https://github.com/Clinical-Genomics/genotype
[chanjo]: https://github.com/Clinical-Genomics/chanjo
[scout]: https://github.com/Clinical-Genomics/scout
[mip]: https://github.com/Clinical-Genomics/mip
[scilife]: https://www.scilifelab.se/
[flask]: http://flask.pocoo.org/
[click]: http://click.pocoo.org/5/
[cgweb]: https://github.com/Clinical-Genomics/cgweb
[servers]: https://github.com/Clinical-Genomics/servers
[snapshottest]: https://github.com/syrusakbary/snapshottest
