
-- change name of name column to shortname in bed-version
ALTER TABLE `bed_version` CHANGE COLUMN `description` `shortname` varchar(64);

