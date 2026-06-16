CREATE TABLE IF NOT EXISTS app_auth (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF to_regclass('public.app_auth') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_app_auth_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_app_auth_updated_at
                 BEFORE UPDATE ON app_auth
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;
END
$$;
