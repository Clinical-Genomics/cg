# cg

`cg` stands for Clinical Genomics. We are the clinical sequencing platform under SciLifeLab's umbrella of facilities.

This is our main package for interacting with the data and samples that flow through our pipeline. We rely on a set of specialized "apps" to deal with a lot of the complexity like:

- [Trailblazer][trailblazer] - for interacting with MIP, the rare disease analysis pipeline
- [Housekeeper][housekeeper] - for storing and archiving valuable data
- [Genotype][genotype] - for keeping track of samples so we don't mix anything up

In this context, `cg` provides the interface between these tools to facilitate automation and other necessary cross-talk. It also exposes some APIs:

- HTTP REST for powering the `cgweb` web application
- CLI for interactions on the command line


[trailblazer]: https://github.com/Clinical-Genomics/trailblazer
[housekeeper]: https://github.com/Clinical-Genomics/housekeeper
[genotype]: https://github.com/Clinical-Genomics/genotype
