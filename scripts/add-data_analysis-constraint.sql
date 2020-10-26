
Update `family` SET data_analysis = 'mip-dna' where data_analysis like 'mip';
Update `family` SET data_analysis = 'mip-rna' where data_analysis like 'mip + rna';
Update `family` SET data_analysis = 'balsamic' where data_analysis like 'balsamic';
Update `family` SET data_analysis = 'fastq' where data_analysis like 'fastq';
Update `family` SET data_analysis = 'mip-rna' where data_analysis like 'mip rna';
Update `family` SET data_analysis = 'microbial' where data_analysis like 'microbial';
Update `family` SET data_analysis = 'microbial' where data_analysis like 'microbial|fastq';
Update `family` SET data_analysis = 'microbial' where data_analysis like 'microbial|custom';

ALTER TABLE `family` CHANGE `data_analysis` `data_analysis` ENUM('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;

ALTER TABLE `analysis` CHANGE `pipeline` `pipeline` ENUM('balsamic', 'fastq', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;
