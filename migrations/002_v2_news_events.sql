-- 002: V2 news/event calendar (manual input + CSV path).
-- MVP behavior unchanged: without rows, the news filter reports OFF.

CREATE TABLE IF NOT EXISTS economic_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  currency CHAR(3) NOT NULL,
  event_name VARCHAR(255) NOT NULL,
  impact VARCHAR(20) NOT NULL DEFAULT 'low',
  scheduled_at TIMESTAMPTZ NOT NULL,
  actual_value TEXT,
  forecast_value TEXT,
  previous_value TEXT,
  source VARCHAR(100) NOT NULL DEFAULT 'manual',
  external_id VARCHAR(150),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, external_id)
);
CREATE INDEX IF NOT EXISTS economic_events_currency_scheduled
  ON economic_events (currency, scheduled_at);
