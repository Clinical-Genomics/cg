UPDATE customer SET invoice_address='' WHERE invoice_address IS NULL
UPDATE customer SET invoice_reference='' WHERE invoice_reference IS NULL
ALTER TABLE customer ALTER COLUMN invoice_address TEXT NOT NULL
ALTER TABLE customer ALTER COLUMN invoice_reference STRING(32) NOT NULL
