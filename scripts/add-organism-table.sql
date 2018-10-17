CREATE TABLE `organism` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `internal_id` varchar(32) NOT NULL UNIQUE,
  `name` varchar(255) NOT NULL UNIQUE,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `reference_genome` varchar(255) DEFAULT NULL,
  `verified` tinyint(1) DEFAULT '0',
  `comment` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

# add some test data
INSERT INTO `cg-dev`.organism (name, internal_id, created_at, reference_genome)
    SELECT strain, strain, now(), reference_genome
    FROM microbial_sample
    where strain is not null and strain <> 'Other'
    and strain NOT IN (SELECT name
                   FROM organism)
    GROUP BY strain;

# add some test data
INSERT INTO `cg-dev`.organism (name, internal_id, created_at, reference_genome)
    SELECT strain_other, strain_other, now(), reference_genome
    FROM microbial_sample
    where strain = 'Other'
    and strain_other is not null
    and strain_other NOT IN (SELECT name
                       FROM organism)
    GROUP BY strain_other;

ALTER TABLE microbial_sample ADD COLUMN organism_id INTEGER NULL;

Update microbial_sample SET organism_id = ( SELECT id FROM organism Where internal_id = microbial_sample.strain and reference_genome = microbial_sample.reference_genome ) Where organism_id is null;
Update microbial_sample SET organism_id = ( SELECT id FROM organism Where internal_id = microbial_sample.strain_other and reference_genome = microbial_sample.reference_genome ) Where organism_id is null;

ALTER TABLE microbial_sample ADD CONSTRAINT `organism_ibfk_1` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`);

# delete strain column in microbial_samples
ALTER TABLE microbial_sample DROP COLUMN strain;
