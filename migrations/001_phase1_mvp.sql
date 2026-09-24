-- 001_phase1_mvp.sql — MVP Phase 1 (PostgreSQL). Spec: DATABASE.md #47.
-- V2 tables (trading_accounts, trades, backtests, economic_events, ...) menyusul.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- USERS
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(150) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- CURRENCY PAIRS
CREATE TABLE currency_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol VARCHAR(20) NOT NULL UNIQUE,
  base_currency CHAR(3) NOT NULL,
  quote_currency CHAR(3) NOT NULL,
  instrument_type VARCHAR(30) NOT NULL DEFAULT 'forex',
  pip_size NUMERIC(20,10) NOT NULL,
  contract_size NUMERIC(20,8) NOT NULL,
  price_precision SMALLINT NOT NULL DEFAULT 5,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- MARKET CANDLES (immutable raw)
CREATE TABLE market_candles (
  id BIGSERIAL PRIMARY KEY,
  currency_pair_id UUID NOT NULL REFERENCES currency_pairs(id),
  timeframe VARCHAR(10) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  open NUMERIC(20,10) NOT NULL,
  high NUMERIC(20,10) NOT NULL,
  low NUMERIC(20,10) NOT NULL,
  close NUMERIC(20,10) NOT NULL,
  volume NUMERIC(30,10) NOT NULL DEFAULT 0,
  source VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (currency_pair_id, timeframe, timestamp, source)
);
CREATE INDEX ON market_candles (currency_pair_id, timeframe, timestamp DESC);

-- MARKET SESSIONS
CREATE TABLE market_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) NOT NULL,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RISK PROFILES
CREATE TABLE risk_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(100) NOT NULL,
  risk_per_trade_pct NUMERIC(8,4) NOT NULL,
  max_daily_loss_pct NUMERIC(8,4) NOT NULL,
  max_open_positions INTEGER NOT NULL DEFAULT 3,
  max_exposure_pct NUMERIC(8,4) NOT NULL,
  min_risk_reward NUMERIC(8,4) NOT NULL DEFAULT 2.0,
  max_spread NUMERIC(20,8) NOT NULL,
  max_position_size NUMERIC(20,8) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- STRATEGIES (versioned; condition JSONB in rules, no strategy_conditions table)
CREATE TABLE strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(150) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  direction VARCHAR(20) NOT NULL DEFAULT 'both',
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE strategy_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES strategies(id),
  version_number INTEGER NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  configuration JSONB NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (strategy_id, version_number)
);
CREATE TABLE strategy_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_version_id UUID NOT NULL REFERENCES strategy_versions(id),
  rule_type VARCHAR(50) NOT NULL,
  name VARCHAR(150) NOT NULL,
  condition JSONB NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  weight NUMERIC(8,4) NOT NULL DEFAULT 1.0,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ANALYSIS SNAPSHOT
CREATE TABLE market_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  currency_pair_id UUID NOT NULL REFERENCES currency_pairs(id),
  timeframe VARCHAR(10) NOT NULL,
  candle_timestamp TIMESTAMPTZ NOT NULL,
  bias VARCHAR(20) NOT NULL,
  trend_state VARCHAR(30) NOT NULL DEFAULT 'unknown',
  momentum_state VARCHAR(30) NOT NULL DEFAULT 'unknown',
  volatility_state VARCHAR(30) NOT NULL DEFAULT 'unknown',
  data_quality VARCHAR(30) NOT NULL DEFAULT 'ok',
  engine_version VARCHAR(50) NOT NULL DEFAULT 'mvp1',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON market_analyses (currency_pair_id, timeframe, candle_timestamp DESC);
CREATE TABLE market_structures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  market_analysis_id UUID NOT NULL REFERENCES market_analyses(id),
  structure_type VARCHAR(50) NOT NULL,
  direction VARCHAR(20) NOT NULL,
  swing_price NUMERIC(20,10) NOT NULL,
  swing_timestamp TIMESTAMPTZ NOT NULL,
  strength VARCHAR(20) NOT NULL DEFAULT 'weak',
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE indicator_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  market_analysis_id UUID NOT NULL REFERENCES market_analyses(id),
  indicator VARCHAR(50) NOT NULL,
  parameters JSONB NOT NULL DEFAULT '{}',
  value NUMERIC(30,12),
  secondary_value NUMERIC(30,12),
  state VARCHAR(50) NOT NULL DEFAULT 'unknown',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE market_zones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  currency_pair_id UUID NOT NULL REFERENCES currency_pairs(id),
  timeframe VARCHAR(10) NOT NULL,
  zone_type VARCHAR(50) NOT NULL,
  price_low NUMERIC(20,10) NOT NULL,
  price_high NUMERIC(20,10) NOT NULL,
  strength VARCHAR(20) NOT NULL DEFAULT 'moderate',
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  invalidated_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- SETUPS + CONFIRMATIONS + RISK CHECKS
CREATE TABLE setups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  currency_pair_id UUID NOT NULL REFERENCES currency_pairs(id),
  strategy_version_id UUID NOT NULL REFERENCES strategy_versions(id),
  market_analysis_id UUID REFERENCES market_analyses(id),
  direction VARCHAR(10) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'candidate',
  entry_min NUMERIC(20,10),
  entry_max NUMERIC(20,10),
  stop_loss NUMERIC(20,10),
  take_profit NUMERIC(20,10),
  risk_reward NUMERIC(12,6),
  quality VARCHAR(30) NOT NULL DEFAULT 'unknown',
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  invalidated_at TIMESTAMPTZ,
  invalidation_reason TEXT,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON setups (currency_pair_id, status, detected_at DESC);
CREATE TABLE setup_confirmations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  setup_id UUID NOT NULL REFERENCES setups(id),
  confirmation_type VARCHAR(50) NOT NULL,
  status VARCHAR(30) NOT NULL,
  strength VARCHAR(30) NOT NULL DEFAULT 'moderate',
  score NUMERIC(8,4),
  evidence JSONB NOT NULL DEFAULT '{}',
  missing_reason TEXT,
  evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE risk_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  setup_id UUID NOT NULL REFERENCES setups(id),
  risk_profile_id UUID NOT NULL REFERENCES risk_profiles(id),
  risk_amount NUMERIC(20,8),
  risk_percent NUMERIC(12,6),
  position_size NUMERIC(20,8),
  stop_distance NUMERIC(20,10),
  reward_distance NUMERIC(20,10),
  risk_reward NUMERIC(12,6),
  spread NUMERIC(20,10),
  exposure_percent NUMERIC(12,6),
  status VARCHAR(20) NOT NULL,
  failures JSONB NOT NULL DEFAULT '[]',
  evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- SIGNALS (decision immutable, status mutable lifecycle)
CREATE TABLE signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  setup_id UUID NOT NULL REFERENCES setups(id),
  user_id UUID NOT NULL REFERENCES users(id),
  decision VARCHAR(20) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'generated',
  direction VARCHAR(10) NOT NULL,
  strategy_version_id UUID NOT NULL REFERENCES strategy_versions(id),
  decision_reason JSONB NOT NULL DEFAULT '{}',
  confirmation_snapshot JSONB NOT NULL DEFAULT '{}',
  risk_snapshot JSONB NOT NULL DEFAULT '{}',
  analysis_snapshot JSONB NOT NULL DEFAULT '{}',
  engine_version VARCHAR(50) NOT NULL DEFAULT 'mvp1',
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  status_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON signals (user_id, decision, generated_at DESC);
CREATE INDEX ON signals (setup_id, status);

-- AUDIT
CREATE TABLE decision_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id UUID NOT NULL REFERENCES signals(id),
  engine_version VARCHAR(50) NOT NULL,
  input_snapshot JSONB NOT NULL,
  decision VARCHAR(20) NOT NULL,
  reasoning_snapshot JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ALERTS (MVP in-app only)
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  currency_pair_id UUID REFERENCES currency_pairs(id),
  strategy_id UUID REFERENCES strategies(id),
  alert_type VARCHAR(50) NOT NULL,
  conditions JSONB NOT NULL DEFAULT '{}',
  channel VARCHAR(30) NOT NULL DEFAULT 'in-app',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE alert_events (
  id BIGSERIAL PRIMARY KEY,
  alert_id UUID NOT NULL REFERENCES alerts(id),
  triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL DEFAULT '{}',
  delivery_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- MVP SEED: pairs
INSERT INTO currency_pairs (symbol, base_currency, quote_currency, instrument_type, pip_size, contract_size, price_precision) VALUES
  ('EUR/USD', 'EUR', 'USD', 'forex', 0.0001, 100000, 5),
  ('GBP/USD', 'GBP', 'USD', 'forex', 0.0001, 100000, 5),
  ('USD/JPY', 'USD', 'JPY', 'forex', 0.01, 100000, 3),
  ('XAU/USD', 'XAU', 'USD', 'gold', 0.01, 100, 2)
ON CONFLICT (symbol) DO NOTHING;
