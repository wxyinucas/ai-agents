-- Explicit teacher setup only. No existing application tables are changed.
CREATE SCHEMA IF NOT EXISTS w08_demo;

CREATE TABLE IF NOT EXISTS w08_demo.batches (
    dataset text PRIMARY KEY,
    batch_id text NOT NULL,
    generated_at timestamptz NOT NULL,
    config jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS w08_demo.measurements (
    dataset text NOT NULL REFERENCES w08_demo.batches(dataset) ON DELETE CASCADE,
    sample_id integer NOT NULL,
    x double precision NOT NULL,
    y double precision NOT NULL,
    PRIMARY KEY (dataset, sample_id)
);
