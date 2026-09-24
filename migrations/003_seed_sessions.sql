-- 003: seed reference trading sessions (UTC, informational for scanner).
-- Hours follow the standard forex session map; DST shifts ignored (documented).
-- Idempotent: only inserts names that are missing.

INSERT INTO market_sessions (name, timezone, start_time, end_time)
SELECT v.name, v.timezone, v.start_time::time, v.end_time::time
FROM (VALUES
  ('Sydney', 'UTC', '21:00', '06:00'),
  ('Tokyo', 'UTC', '00:00', '09:00'),
  ('London', 'UTC', '08:00', '17:00'),
  ('New York', 'UTC', '13:00', '22:00')
) AS v(name, timezone, start_time, end_time)
WHERE NOT EXISTS (SELECT 1 FROM market_sessions m WHERE m.name = v.name);
