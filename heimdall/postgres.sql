-- Run as a dedicated migration administrator, never as the runtime login.
-- Roles intentionally have no passwords. Provision a separate runtime LOGIN.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'heimdall_owner') THEN
    CREATE ROLE heimdall_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'heimdall_runtime') THEN
    CREATE ROLE heimdall_runtime NOLOGIN;
  END IF;
END $$;
-- Cloud SQL migration administrators are not superusers; allow SET ROLE.
-- This grants owner membership only to the migration identity, never runtime.
GRANT heimdall_owner TO CURRENT_USER;
CREATE SCHEMA IF NOT EXISTS heimdall AUTHORIZATION heimdall_owner;
SET LOCAL ROLE heimdall_owner;
CREATE TABLE IF NOT EXISTS heimdall.events (
  seq bigint PRIMARY KEY, body text NOT NULL, previous text NOT NULL, digest text NOT NULL
);
CREATE TABLE IF NOT EXISTS heimdall.items (
  key text PRIMARY KEY, payload text NOT NULL, policy text NOT NULL,
  result text NOT NULL, status text NOT NULL
);
CREATE OR REPLACE FUNCTION heimdall.append_event(event_body text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, heimdall AS $$
DECLARE r record; n bigint := 1; prev text := repeat('0',64); hash text;
BEGIN
  PERFORM pg_advisory_xact_lock(515408, 1);
  FOR r IN SELECT * FROM heimdall.events ORDER BY seq LOOP
    hash := encode(sha256(convert_to(r.seq::text || ':' || r.previous || ':' || r.body, 'UTF8')), 'hex');
    IF r.seq <> n OR r.previous <> prev OR r.digest <> hash THEN
      RAISE EXCEPTION 'audit chain integrity failure';
    END IF;
    prev := r.digest; n := n + 1;
  END LOOP;
  hash := encode(sha256(convert_to(n::text || ':' || prev || ':' || event_body, 'UTF8')), 'hex');
  INSERT INTO heimdall.events VALUES (n, event_body, prev, hash);
END $$;
CREATE OR REPLACE FUNCTION heimdall.protect_events() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN RAISE EXCEPTION 'append-only audit'; END $$;
DROP TRIGGER IF EXISTS protect_events ON heimdall.events;
CREATE TRIGGER protect_events BEFORE UPDATE OR DELETE OR TRUNCATE ON heimdall.events
FOR EACH STATEMENT EXECUTE FUNCTION heimdall.protect_events();
CREATE OR REPLACE FUNCTION heimdall.record_state() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, heimdall AS $$
BEGIN
  IF TG_OP IN ('DELETE', 'TRUNCATE') THEN RAISE EXCEPTION 'lifecycle deletion forbidden'; END IF;
  IF TG_OP = 'UPDATE' AND (NEW.key <> OLD.key OR NEW.payload <> OLD.payload OR NEW.policy <> OLD.policy
      OR OLD.status <> 'pending' OR NEW.status NOT IN ('denied','blocked','approved_simulated')) THEN
    RAISE EXCEPTION 'invalid lifecycle transition';
  END IF;
  PERFORM heimdall.append_event(json_build_object('type','state','row',row_to_json(NEW))::text);
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS record_state ON heimdall.items;
CREATE TRIGGER record_state AFTER INSERT OR UPDATE OR DELETE ON heimdall.items
FOR EACH ROW EXECUTE FUNCTION heimdall.record_state();
DROP TRIGGER IF EXISTS no_truncate_items ON heimdall.items;
CREATE TRIGGER no_truncate_items BEFORE TRUNCATE ON heimdall.items
FOR EACH STATEMENT EXECUTE FUNCTION heimdall.protect_events();
REVOKE ALL ON SCHEMA heimdall FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA heimdall FROM PUBLIC, heimdall_runtime;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA heimdall FROM PUBLIC, heimdall_runtime;
GRANT USAGE ON SCHEMA heimdall TO heimdall_runtime;
GRANT SELECT ON heimdall.events TO heimdall_runtime;
GRANT SELECT, INSERT ON heimdall.items TO heimdall_runtime;
GRANT UPDATE (result, status) ON heimdall.items TO heimdall_runtime;
GRANT EXECUTE ON FUNCTION heimdall.append_event(text) TO heimdall_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA heimdall REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
COMMIT;
