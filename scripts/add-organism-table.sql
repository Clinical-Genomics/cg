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

# add the OF organisms
INSERT INTO `cg-dev`.organism (name, internal_id, created_at)
    VALUES ('C. jejuni', 'C. jejuni', now()),
    ('C. difficile', 'C. difficile', now()),
    ('E. faecalis', 'E. faecalis', now()),
    ('E. faecium', 'E. faecium', now()),
    ('E. coli', 'E. coli', now()),
    ('K. pneumoniae', 'K. pneumoniae', now()),
    ('M. tuberculosis', 'M. tuberculosis', now()),
    ('N. gonorrhoeae', 'N. gonorrhoeae', now()),
    ('P. aeruginosa', 'P. aeruginosa', now()),
    ('S. aureus', 'S. aureus', now()),
    ('S. agalactiae', 'S. agalactiae', now()),
    ('S. pneumoniae', 'S. pneumoniae', now()),
    ('S. pyogenes', 'S. pyogenes', now());

# add used organisms
INSERT INTO `cg-dev`.organism (name, internal_id, created_at, reference_genome, verified)
    SELECT strain, strain, now(), reference_genome, 0
    FROM microbial_sample
    where strain is not null and strain <> 'Other'
    and strain NOT IN (SELECT name
                   FROM organism)
    GROUP BY strain;

# add used other organisms
INSERT INTO `cg-dev`.organism (name, internal_id, created_at, reference_genome)
    SELECT strain_other, strain_other, now(), reference_genome
    FROM microbial_sample
    where strain = 'Other'
    and strain_other is not null
    and strain_other NOT IN (SELECT name
                       FROM organism)
    GROUP BY strain_other;

# set reference genomes for the organisms
UPDATE `cg-dev`.organism as o
  join microbial_sample ms on ms.strain = o.name
set
  o.reference_genome = ms.reference_genome
where
  o.reference_genome is null;

ALTER TABLE microbial_sample ADD COLUMN organism_id INTEGER NULL;

Update microbial_sample SET organism_id = ( SELECT id FROM organism Where internal_id = microbial_sample.strain and reference_genome = microbial_sample.reference_genome ) Where organism_id is null;
Update microbial_sample SET organism_id = ( SELECT id FROM organism Where internal_id = microbial_sample.strain_other and reference_genome = microbial_sample.reference_genome ) Where organism_id is null;

ALTER TABLE microbial_sample ADD CONSTRAINT `organism_ibfk_1` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`);

# delete strain column in microbial_samples
ALTER TABLE microbial_sample DROP COLUMN strain;
ALTER TABLE microbial_sample DROP COLUMN strain_other;
ALTER TABLE microbial_sample CHANGE `organism_id` `organism_id` INTEGER NOT NULL;