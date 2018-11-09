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
