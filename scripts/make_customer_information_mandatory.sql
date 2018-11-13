UPDATE customer SET invoice_address="" WHERE invoice_address IS NULL;
UPDATE customer SET invoice_reference="" WHERE invoice_reference IS NULL;
ALTER TABLE customer MODIFY COLUMN invoice_address text NOT NULL;
ALTER TABLE customer MODIFY COLUMN invoice_reference varchar(32) NOT NULL;

ALTER TABLE customer ADD COLUMN delivery_contact_id int NULL;	
Update customer SET delivery_contact_id = ( SELECT id FROM user Where email = customer.delivery_contact ) Where delivery_contact_id is NULL;	
ALTER TABLE customer ADD CONSTRAINT `delivery_contact_ibfk_1` FOREIGN KEY (`delivery_contact_id`) REFERENCES `user` (`id`);	
ALTER TABLE customer DROP COLUMN delivery_contact	

ALTER TABLE customer ADD COLUMN invoice_contact_id int NULL;	
Update customer SET invoice_contact_id = ( SELECT id FROM user Where email = customer.invoice_contact ) Where invoice_contact_id is NULL;	
ALTER TABLE customer ADD CONSTRAINT `invoice_contact_ibfk_1` FOREIGN KEY (`invoice_contact_id`) REFERENCES `user` (`id`);	
ALTER TABLE customer DROP COLUMN invoice_contact	

ALTER TABLE customer ADD COLUMN primary_contact_id int NULL;	
Update customer SET primary_contact_id = ( SELECT id FROM user Where email = customer.primary_contact ) Where primary_contact_id is NULL;	
ALTER TABLE customer ADD CONSTRAINT `primary_contact_ibfk_1` FOREIGN KEY (`primary_contact_id`) REFERENCES `user` (`id`);	
ALTER TABLE customer DROP COLUMN primary_contact
