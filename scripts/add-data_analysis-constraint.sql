ALTER TABLE `family`
ADD COLUMN `data_delivery` ENUM('fastq', 'qc', 'standard')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL
 DEFAULT 'standard';

Update `family` SET data_delivery = 'qc' where data_analysis like 'microbial|fastq';
Update `family` SET data_delivery = 'standard' where data_analysis like 'microbial|custom';
Update `family` SET data_delivery = 'fastq' where data_analysis like 'fastq';

Update `family` SET data_analysis = 'mip-dna' where data_analysis like 'mip';
Update `family` SET data_analysis = 'mip-dna' where data_analysis like 'mip';
Update `family` SET data_analysis = 'mip-rna' where data_analysis like 'mip + rna';
Update `family` SET data_analysis = 'balsamic' where data_analysis like 'balsamic';
Update `family` SET data_analysis = 'fastq' where data_analysis like 'fastq';
Update `family` SET data_analysis = 'mip-rna' where data_analysis like 'mip rna';
Update `family` SET data_analysis = 'microsalt' where data_analysis like 'microbial';
Update `family` SET data_analysis = 'microsalt' where data_analysis like 'microbial|fastq';
Update `family` SET data_analysis = 'microsalt' where data_analysis like 'microbial|custom';
-- Update `family` SET data_analysis = 'mip-dna' where data_analysis is null;

select * from family where family.data_analysis not in ('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna');

ALTER TABLE `family` CHANGE `data_analysis` `data_analysis` ENUM('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;

Update `analysis` SET pipeline = 'balsamic' where pipeline like 'Balsamic';
Update `analysis` SET pipeline = 'mip-dna' where pipeline like 'mip';

select * from analysis where analysis.pipeline not in ('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna');

ALTER TABLE `analysis` CHANGE `pipeline` `pipeline` ENUM('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;

-- drop deprecated fields
ALTER TABLE `analysis` DROP COLUMN `microbial_order_id`;
ALTER TABLE `application` DROP COLUMN `category`;

select distinct data_delivery from family;
select distinct data_analysis from family;
select distinct pipeline from analysis;

