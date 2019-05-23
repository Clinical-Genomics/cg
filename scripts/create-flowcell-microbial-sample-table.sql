CREATE TABLE `flowcell_microbial_sample` (
  `flowcell_id` int(11) NOT NULL,
  `microbial_sample_id` int(11) NOT NULL,
  UNIQUE KEY `_flowcell_sample_uc` (`flowcell_id`,`microbial_sample_id`),
  KEY `microbial_sample_id` (`microbial_sample_id`),
  CONSTRAINT `flowcell_microbial_sample_ibfk_1` FOREIGN KEY (`flowcell_id`) REFERENCES `flowcell` (`id`),
  CONSTRAINT `flowcell_microbial_sample_ibfk_2` FOREIGN KEY (`microbial_sample_id`) REFERENCES `microbial_sample` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
