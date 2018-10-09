UPDATE customer SET invoice_address="" WHERE invoice_address IS NULL;
UPDATE customer SET invoice_reference="" WHERE invoice_reference IS NULL;
ALTER TABLE customer MODIFY COLUMN invoice_address text NOT NULL;
ALTER TABLE customer MODIFY COLUMN invoice_reference varchar(32) NOT NULL;
