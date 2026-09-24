-- 004: V2 journal entries on Postgres (PG-first, file-store fallback).
-- Links to owned signals when available; paper trades stay referenced via
-- trade_ref TEXT (no FK) because paper ids are short hex, not UUIDs.

CREATE TABLE IF NOT EXISTS journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  signal_id UUID REFERENCES signals(id) ON DELETE CASCADE,
  trade_ref TEXT,
  thesis TEXT NOT NULL DEFAULT '',
  market_context TEXT NOT NULL DEFAULT '',
  entry_reason TEXT NOT NULL DEFAULT '',
  exit_reason TEXT NOT NULL DEFAULT '',
  emotion VARCHAR(50) NOT NULL DEFAULT '',
  lesson TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  decision_snapshot JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS journal_entries_user_created
  ON journal_entries (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS journal_entries_signal
  ON journal_entries (signal_id);
