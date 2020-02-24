-- show data to be removed
select sample.internal_id, sample.ordered_at, sample.sequenced_at, sample.delivered_at, bed.name, bed_version.description, bed_version.filename  from sample
inner join bed_version on bed_version.id = bed_version_id
inner join bed on bed.id = bed_version.bed_id
where bed_version_id is not null
order by sample.ordered_at

-- remove unused columns in bed-version
ALTER TABLE `bed_version` DROP COLUMN `genes`;
ALTER TABLE `bed_version` DROP COLUMN `unique_transcripts`;
ALTER TABLE `bed_version` DROP COLUMN `transcripts_with_all_exons_covered`;
ALTER TABLE `bed_version` DROP COLUMN `transcripts_with_at_least_one_exon_covered`;
ALTER TABLE `bed_version` DROP COLUMN `padding`;
ALTER TABLE `bed_version` DROP COLUMN `cosmic_snps`;
ALTER TABLE `bed_version` DROP COLUMN `non_genic_regions`;
ALTER TABLE `bed_version` DROP COLUMN `independent_segments`;

-- change name of name column to shortname in bed-version
ALTER TABLE `bed_version` CHANGE COLUMN `description` `shortname` varchar(64);

