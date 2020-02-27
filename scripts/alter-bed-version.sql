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

-- remove bed-version from samples
ALTER TABLE sample DROP COLUMN  `bed_version_id` int(11);
