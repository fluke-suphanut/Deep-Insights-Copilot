Set-Content -Path .\seed.sql -Value @"
CREATE SCHEMA IF NOT EXISTS public;
SET search_path TO public;

CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT,
  segment TEXT,
  joined_at DATE
);

CREATE TABLE IF NOT EXISTS tickets (
  id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  product TEXT,
  category TEXT,
  issue TEXT,
  status TEXT,
  created_at DATE
);

CREATE TABLE IF NOT EXISTS products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  category TEXT,
  release_date DATE
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uniq_customer_name_joined')
  THEN ALTER TABLE customers ADD CONSTRAINT uniq_customer_name_joined UNIQUE (name, joined_at); END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uniq_product_name_release')
  THEN ALTER TABLE products  ADD CONSTRAINT uniq_product_name_release UNIQUE (name, release_date); END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uniq_ticket_sig')
  THEN ALTER TABLE tickets   ADD CONSTRAINT uniq_ticket_sig UNIQUE (customer_id, product, category, issue, status, created_at); END IF;
END$$;

INSERT INTO customers (name, segment, joined_at) VALUES
('Alice','Retail','2023-01-10'),
('Bob','Corporate','2023-03-14'),
('Charlie','Retail','2022-11-01')
ON CONFLICT ON CONSTRAINT uniq_customer_name_joined DO NOTHING;

INSERT INTO products (name, category, release_date) VALUES
('Virtual Bank App v1.0','Digital Saving','2023-05-01'),
('Virtual Bank App v1.2','Digital Lending','2024-02-01')
ON CONFLICT ON CONSTRAINT uniq_product_name_release DO NOTHING;

INSERT INTO tickets (customer_id, product, category, issue, status, created_at) VALUES
(1,'Virtual Bank App v1.2','App Crash','App crashes on login','open','2025-09-01'),
(1,'Virtual Bank App v1.2','App Crash','App crashes on login','open','2025-09-05'),
(2,'Virtual Bank App v1.0','Login','Login OTP delay','closed','2025-09-02'),
(2,'Virtual Bank App v1.0','Performance','Slow transaction loading','open','2025-09-07'),
(3,'Virtual Bank App v1.2','UI Bug','Misaligned button','open','2025-09-03')
ON CONFLICT ON CONSTRAINT uniq_ticket_sig DO NOTHING;
"@
