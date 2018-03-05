# Analysis

   1. [Config](#1-config)

## 1. Config
Generate a MIP pedigree.yaml file for the FAMILY_ID and place it in the trailblazer root directory.

#### Command
```Bash
$ cg analysis config [OPTIONS] FAMILY_ID
```
#### Input
- FAMILY_ID: `<Petname_family_id>`

#### Databases
- cg

#### Apps
- Trailblazer

#### Action
- Collect `<Petname_family_id>` meta data from the `cg` database.
- Validate the meta data, handle single cases with unknown phenotype and reformat to MIP pedigree.yaml format via `trailblazer`.

#### Output
- [pedigree.yaml](https://github.com/Clinical-Genomics/MIP/blob/master/templates/643594-miptest_pedigree.yaml) file in MIP format in the trailblazer root directory
