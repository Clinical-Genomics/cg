# cg commands
This is documentation for cg commands.

Recurring nomenclature:
- sample_id = internal sampleID, provided by LIMS: `ADM..`
- ext_sample_id = external sampleID, provided by customer: `customer's sample_id`
- customer_id = `custxxx`
- ticket_id = `898988`
- family_id = `cuddlygull`

## cg add
Add new things to statusDB.

### cg add customer
Add a new customer with a unique INTERNAL_ID and NAME.

```$ cg add customer CUSTOMER_ID CUSTOMER_NAME```

where `CUSTOMER_ID` our internal customer ID, e.g. cust000, and `CUSTOMER_NAME` is the customer name, e.g. institute or P.I.

### cg add family
Add a family to CUSTOMER_ID with a NAME.

```$ cg add family CUSTOMER_ID FAMILY_NAME```

where `FAMILY_NAME` is the customer's familyID.

It is required to supply a panel.

```$ cg add family --panel PANEL CUSTOMER_ID FAMILY_NAME```

where `PANEL` are the gene panels. To add multiple panels simply provide `--panel PANEL` again with another gene panel.

When adding a family, set the priority by using

```$ cg add family --priority PRIORITY CUSTOMER_ID FAMILY_NAME```

where `PRIORITY` could be `low`, `normal`, or `high`.

### cg add relationship
Create a link between a FAMILY_ID and a SAMPLE_ID.

```$ cg add relationship FAMILY_ID SAMPLE_ID```

where `FAMILY_ID` is our internal family ID, e.g. `cuddlygull`.

It is required to set the status.

```cg add relationship --status STATUS FAMILY_ID SAMPLE_ID```

where `STATUS` can be `affected`, `unaffected`, or `unknown`.

Add relationship between parents using the `--mother` and `--father` flags. Example:

```$ cg add relationship --mother MOTHER_ID FAMILY_ID SAMPLE_ID```

where `MOTHER_ID` is the sampleID for the mother of the child sample.

### cg add sample
Add a sample for CUSTOMER_ID with a SAMPLE_NAME.

```$ cg add sample CUSTOMER_ID SAMPLE_NAME```

where `SAMPLE_NAME` is the customer's sampleID.

It is required to set the gender of the sample.

```$ cg add sample --sex SEX CUSTOMER_ID SAMPLE_NAME```

where `SEX`can be `male`, `female`, or `unknown`.

It is also required to set the application tag.

```$ cg add sample --application APP_TAG CUSTOMER_ID SAMPLE_NAME```

where `APP_TAG` is the application tag.

Add a LIMS id by using the ´--lims´ flag.

```$ cg add sample --lims LIMS_ID CUSTOMER_ID SAMPLE_NAME```

Add the order the sample belongs to by using the `--order` flag.

```$ cg add sample --order TICKET_ID CUSTOMER_ID SAMPLE_NAME```

Add the priority of the sample by using the `--priority` flag.

```$ cg add sample --priority PRIORITY CUSTOMER_ID SAMPLE_NAME```

where `PRIORITY` can be `research`, `standard`, `priority`, or `express`.

In case that the sample has been downsampled, provide how many reads it has been downsampled to.

```$ cg add sample --downsampled INTEGER CUSTOMER_ID SAMPLE_NAME```

### cg add user
Add a new user with an EMAIL (login) and a NAME (full). ```$ cg add user EMAIL NAME```

It is required to connect the user to a customer. ```$ cg add user --customer CUSTOMER_ID EMAIL NAME```

To give a user admin rights, use the `--admin` flag. ```$ cg add user --admin EMAIL NAME```

## cg analysis
Prepare and start a MIP analysis for a case. To do this use

```$ cg analysis --family FAMILY_ID```

where `FAMILY_ID` is the case name, e.g. `cuddlygull`.

Using this option will overwrite any configuration files, so if changes has been made to these that should be kept, use instead `cg analysis start`.

To change the quality of service for an analysis use

```$ cg analysis --family FAMILY_ID --priority PRIORITY```

where `PRIORITY` could be `low`, `normal`, or `high`. The default is set in statusDB.

Notification of errors will by default be sent to the email of the user who started the analysis. To change the email use

```$ cg analysis --family FAMILY_ID --email TEXT```

where `TEXT` is the email address.

### cg analysis auto
Start all analyses that are ready for analysis.

### cg analysis config
Generate a configuration file (pedigree.yaml) for an analysis.

```$ cg analysis config FAMILY_ID```

To print the config to console, rather then creating the `pedigree.yaml`, use the `--dry` flag:

```$ cg analysis config --dry FAMILY_ID```

### cg analysis link
Link FASTQ files for a sample.

```$ cg analysis SAMPLE_ID```

To link files for an entire case, use the `--family` flag:

```$ cg analysis link --family FAMILY_ID```

### cg analysis panel
Write aggregated gene panel file.

```$ cg analysis panel FAMILY_ID```

To only print the panel to console, rather than saving it to a file, use the `--print` flag:

```$ cg analysis panel --print FAMILY_ID```

### cg analysis start
Start the analysis pipeline for a family.

```$ cg analysis start FAMILY_ID```

To change the quality of servive for an analysis use

```$ cg analysis start --priority PRIORITY FAMILY_ID```

where `PRIORITY` could be `low`, `normal`, or `high`. The default is set in statusDB.

## cg backup
Backup utilities.

### cg backup fetch-flowcell
Fetch the first flowcell in the requested queue from backup.

```$ cg backup fetch-flowcell --flowcell FLOWCELL_ID```

## cg clean
Remove stuff. *Use caution.*

### cg clean mip
Remove analysis output. Removes the family directory (as defined in the cg config).

```$ cg clean mip SAMPLE_INFO```

where `SAMPLE_INFO` is the path to the familyID_qc_sample_info.yaml file

There is an option to skip confirmation: `--yes`

### cg clean mipauto
Automatically clean up "old" analyses. Removes all the family directories before the date defined by the user.

```$ cg clean mipauto BEFORE_STR```

where `BEFORE_STR` is a date in string format, e.g. `2018-04-19`

There is an option to skip confirmation: `--yes`

### cg clean scout
Cleans the bam and bai files of selected bundle in housekeeper.

```$ cg clean scout BUNDLE```

There is an option to skip confirmation: `--yes`

### cg clean scoutauto
Automatically clean up solved and archived scout cases. Cleans the bam and bai files in housekeeper.

```cg clean scoutauto```

## cg deliver
Deliver stuff.

### cg deliver inbox
Link files from HK to customer inbox.

```$ cg deliver inbox FAMILY_ID```

where `FAMILY_ID` is the case name, e.g. `cuddlygull`.

`--dry` flag has not been implemented yet.

To just deliver a specific analysis version, use the `--version` flag, example:

```$ cg deliver inbox --version 2018-04-19 FAMILY_ID```

To only link specific types of files from HK, tags can be employed:

```$ cg deliver inbox --tag TAG FAMILY_ID``` where `TAG` are the housekeeper tag(s)

If you want to deliver to another customer inbox than stated in statusDB, use

```$ cg deliver inbox --inbox CUSTOMER_ID FAMILY_ID```

where `CUSTOMER_ID` is the customerID.

## cg get
Get information about records in the database.

The option `-i` makes a guess what type you are looking for.

```$ cg get -i TEXT```

where `TEXT` is a familyID, flowcellID, or sampleID.

### cg get family
Get information about a family.

```$ cg get family FAMILY_ID```

where `FAMILY_ID` is the familyID, e.g. `cuddlygull`.

The same information can be reached using options `--customer` and `--name`, instead of the familyID. Example:

```$ cg get family --name FAMILY_NAME --customer CUSTOMER_ID```

where `FAMILY_NAME` is the customer's internal familyID.

It is possible to toggle if related samples should be shown or not, using `--samples` or `--no-samples`. Example:

```$ cg get family --no-samples FAMILY_ID```

By default the related samples are shown.

### cg get flowcell
Get information about a flowcell and the samples on it.

```$ cg get flowcell FLOWCELL_ID```

It is possible to toggle if related samples should be shown or not , using `--samples` or `--no-samples`. Example:

```$ cg get flowcell --no-samples FLOWCELL_ID```

By default the related samples are shown.

### cg get sample
Get information about a sample.

```$ cg get sample SAMPLE_ID```

It is possible to toggle if related families should be shown or not , using `--families` or `--no-families`. Example:

```$ cg get sample --no-families SAMPLE_ID```

By default the related families are shown.

It is also possible to display related flowcells with the `--flowcells` option.

```$ cg get sample --flowcells SAMPLE_ID```

## cg init

*Do* **not** *touch this, please.*

Setup the database.

```$ cg init```

Options for resetting database before setting up tables (`--reset`) and for bypassing manual confirmation (`--force`).

## cg set
Update information in statusDB.

### cg set family
Update information about a family.

```$ cg set family FAMILY_ID```

where `FAMILY_ID` is the case name, e.g. `cuddlygull`.

To update the analysis action for the family, use

```$ cg set family --action ACTION FAMILY_ID```

where `ACTION` can be `analyze`, `running`, or `hold`.

To update the priority of the analysis, use

```$ cg set family --priority PRIORITY FAMILY_ID```

where `PRIORITY` can be `research`, `standard`, `priority`, or `express`.

To update the gene panel for an analysis, use

```$ cg set family --panel PANEL FAMILY_ID```

where `PANEL` are the gene panels. To add multiple panels simply provide `--panel PANEL` again with another gene panel.

### cg set sample
Update information about a sample.

```$ cg set sample SAMPLE_ID```

To update the gender of a sample, use

```$ cg set sample --sex SEX```

where `SEX`can be `male`, `female`, or `unknown`.

Update the customer, input format `custXXX` with XXX the customer number.
```-c, --customer CUSTOMER_ID```

To append a note/comment to a sample, put text between quotation marks! This will not overwrite the current comment.
```-n, --note TEXT```

Set number of downsampled total reads. Enter 0 to reset.
```-d, --downsampled-to INTEGER```

Set the application tag. Validation of the tag will be performed.
```-a, --application-tag APPLICATION_TAG```

Set the capture kit. NO validation of the kit will be performed.
```-k, --capture-kit CAPTURE_KIT```


## cg status
View status of things.

### cg status analysis
Shows which families will be analyzed.

```$ cg status analysis```

### cg status families
View status of families.

```$ cg status families```

There is an option to skip initial records:

```$ cg status families --skip INTEGER```

where `INTEGER` is the number of lines that should be skipped (shows by default the 30 first entries).

### cg status samples
View status of samples.

```$ cg status samples --skip INTEGER```

where `INTEGER` is the number of lines that should be skipped (shows by default the 30 first entries).

## cg store
Store results from MIP in housekeeper.

### cg store analysis
Store a finished analysis in Housekeeper.

```$ cg store analysis CONFIG_STREAM```

where `CONFIG_STREAM` is the path to the configuration file.

### cg store completed
Store all completed analyses.

```$ cg store completed```

## cg transfer
Transfer results to the status interface.

### cg transfer flowcell
Populate results from a flowcell.

```$ cg transfer flowcell FLOWCELL_ID```

### cg transfer lims
Check if samples have been updated in LIMS.

```$ cg transfer lims --status STATUS```

where `STATUS` can be `received`, `prepared`, or `delivered`.

## cg upload
Upload results from analyses.

To upload analysis results to all the apps, use the flag `--family`. Example:

```$ cg upload --family FAMILY_ID```

where `FAMILY_ID` is our internal familyID, e.g. `cuddlygull`.

### cg upload auto
Upload all completed analyses to all the apps.

```$ cg upload auto```

### cg upload coverage
Upload coverage from an analysis to Chanjo.

```$ cg upload coverage FAMILY_ID```

To re-upload an already existing analysis, use:

```$ cg upload coverage --re-upload FAMILY_ID```

### cg upload genotypes
Upload genotypes from an analysis to Genotype.

```$ cg upload genotypes FAMILY_ID```

### cg upload observations
Upload observations from an analysis to LoqusDB.

```$ cg upload observations FAMILY_ID```

### cg upload scout
Upload variants from analysis to Scout.

```$ cg upload scout FAMILY_ID```

To re-upload already existing analysis to scout, use:

```$ cg upload scout --re-upload FAMILY_ID```

It is possible to get the config values printed to the console:

```$ cg upload scout --print FAMILY_ID```

### cg upload validate
Validate a family of samples.

```$ cg upload validate FAMILY_ID```
