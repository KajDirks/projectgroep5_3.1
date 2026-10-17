-- A tiny "electronic health record" with five (fictional) patients.
-- The values are the 8 inputs the model expects, in the same order as the
-- training data: pregnancies, glucose, diastolic blood pressure, skin
-- thickness, insulin, BMI, diabetes pedigree function, age.
--
-- This file is written for SQLite. Run `python setup_database.py` to turn it
-- into the database file ehr.db.

DROP TABLE IF EXISTS patient;

CREATE TABLE patient (
  id                  INTEGER PRIMARY KEY,   -- filled in automatically
  display_name        TEXT NOT NULL,
  leeft         INTEGER NOT NULL,
  gesl           INTEGER NOT NULL,
  tumsoort   INTEGER NOT NULL,
  diag_basis      INTEGER NOT NULL,
  morf          INTEGER NOT NULL,
  gedrag            INTEGER NOT NULL,
  diffgrad     INTEGER NOT NULL,
  stadium             INTEGER NOT NULL,
  chemo      INTEGER NOT NULL,
  'target'  INTEGER NOT NULL,
  rt       INTEGER NOT NULL,
  SCLC                INTEGER NOT NULL
);

INSERT INTO patient
  (display_name, leeft, gesl,
   tumsoort, diag_basis, morf, gedrag, diffgrad, stadium,
   chemo, 'target', rt, SCLC)
VALUES
  ('Sjoerd de Vries', 53, 1, 302310, 7, 8073, 2, 2, 6, 1, 0, 0, 0),
  ('Xavier Veerman', 24, 1, 302310, 2, 8243, 3, 1, 4, 2, 1, 0, 0),
  ('Sam Hoogendoorn', 44, 2, 302310, 7, 8243, 3, 2, 7, 2, 2, 0, 1),
  ('Brenda van Hoorn', 89, 2, 302310, 2, 8250, 3, 3, 9, 1, 0, 2, 1);
