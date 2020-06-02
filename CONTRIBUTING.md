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
  * [Specs Styleguide](#specs-styleguide)
  * [Documentation Styleguide](#documentation-styleguide)


## Code of Conduct

Communicating around code can be a sensitive thing so please do your best to keep a positive tone. Remember that people are putting significant amount of work behind a PR or a review, stay humble :star:.


## Branch model

Cg is using github flow branching model as described in our [development manual][development-branch-model].


## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for CG. Following these guidelines helps other developers and contributors understand your report :pencil:, reproduce the behavior :computer: :computer:, and find related reports :mag_right:.

Before creating bug reports, please try to search the issues (opened and closed) if the problem has been described before, as you might find out that you don't need to create one. When you are creating a bug report, please [include as many details as possible](#how-do-i-submit-a-good-bug-report).

> **Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one.


#### How Do I Submit A (Good) Bug Report?

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/).

Explain the problem and include additional details to help maintainers reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible. For example, start by explaining where CG was run and how it was used, e.g. which command exactly you used in the terminal.
* **Provide specific examples to demonstrate the steps**. Include links to files or case ids, or copy/pasteable snippets, which you use in those examples. If you're providing snippets in the issue, use [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
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

This section guides you through submitting an enhancement suggestion for CG, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion :pencil: and find related suggestions :mag_right:.


#### How Do I Submit A (Good) Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://guides.github.com/features/issues/). To suggest an enhancement create an issue on that repository and provide the following information:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets which you use in those examples, as [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful**


#### Local development

On our servers where the production and stage versions of CG are run the packages are maintained by using conda environments. For local development it is suggested to follow the [python packaging guidelines](https://packaging.python.org/tutorials/managing-dependencies/) where it is suggested to manage your local python environment with [pipenv](https://pipenv.pypa.io/en/latest/). CG has a Pipfile.lock file which will ensure that the installation will work if the environment is set up in the correct way. To use a **combination of conda and pipenv** make sure that you point to the conda installation of python when creating your pipenv virtual environment (`pipenv --python=$(conda run which python) --site-packages`) more about that [here](https://pipenv.pypa.io/en/latest/advanced/#pipenv-and-other-python-distributions) and in [this](https://stackoverflow.com/questions/50546339/pipenv-with-conda) thread.

When pipenv is install just create a new environment and run `pipenv install`

### Pull Requests

The process described here has several goals:

- Maintain CG's quality
- Engage the developers in working toward the best possible CG
- Enable a sustainable system for CG's maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow all instructions in [the template](.github/PULL_REQUEST_TEMPLATE.md)
2. Follow the [styleguides](#styleguides)
3. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing <details><summary>What if the status checks are failing?</summary>If a status check is failing, and you believe that the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you.</details>

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

#### Python styleguide

We use black to format all files, this is done automatically with each push on GitHub so don't forget to update your local branch with `git pull` after pushing to the origin. More details are described in the general [development manual][development-guidelines].

[development-guidelines]: http://www.clinicalgenomics.se/development/python/conventions/
[development-branch-model]: http://www.clinicalgenomics.se/development/dev/githubflow/
