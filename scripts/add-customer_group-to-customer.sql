ALTER TABLE customer ADD COLUMN customer_group_id INTEGER NOT NULL DEFAULT 0;

CREATE TABLE customer_group (
  id int(11) NOT NULL AUTO_INCREMENT,
  internal_id varchar(32) NOT NULL,
  name varchar(128) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE KEY internal_id (internal_id)
) ENGINE=InnoDB;

INSERT INTO customer_group ( SELECT id, internal_id, name FROM customer );

Update customer SET customer_group_id = ( SELECT id FROM customer_group Where internal_id = customer.internal_id ) Where customer_group_id = 0;
ALTER TABLE customer ADD CONSTRAINT `customer_group_ibfk_1` FOREIGN KEY (`customer_group_id`) REFERENCES `customer_group` (`id`);
