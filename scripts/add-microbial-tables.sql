CREATE TABLE `microbial_order` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `internal_id` varchar(32) DEFAULT NULL,
  `name` varchar(128) NOT NULL,
  `ticket_number` int(11) DEFAULT NULL,
  `comment` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `ordered_at` datetime NOT NULL,
  `customer_id` int(11) NOT NULL,
  `application_version_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `internal_id` (`internal_id`),
  KEY `customer_id` (`customer_id`),
  KEY `application_version_id` (`application_version_id`),
  CONSTRAINT `order_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_ibfk_2` FOREIGN KEY (`application_version_id`) REFERENCES `application_version` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=latin1;


CREATE TABLE `microbial_sample` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `internal_id` varchar(32) NOT NULL,
  `name` varchar(128) NOT NULL,
  `application_version_id` int(11) DEFAULT NULL,
  `microbial_order_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `received_at` datetime DEFAULT NULL,
  `prepared_at` datetime DEFAULT NULL,
  `sequence_start` datetime DEFAULT NULL,
  `sequenced_at` datetime DEFAULT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `reference_genome` varchar(32) DEFAULT NULL,
  `priority` int(11) NOT NULL,
  `reads` bigint(20) DEFAULT NULL,
  `comment` text,
  `invoice_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `internal_id` (`internal_id`),
  KEY `microbial_order_id` (`microbial_order_id`),
  KEY `application_version_id` (`application_version_id`),
  CONSTRAINT `microbial_sample_ibfk_1` FOREIGN KEY (`microbial_order_id`) REFERENCES `microbial_order` (`id`),
  CONSTRAINT `microbial_sample_ibfk_2` FOREIGN KEY (`application_version_id`) REFERENCES `application_version` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=latin1;

