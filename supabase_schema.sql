-- Run this in your Supabase SQL editor (Dashboard → SQL Editor → New query)
-- Creates the two tables Arclat needs. Supabase Auth handles the auth.users table separately.

-- Users table (public profile + API key)
CREATE TABLE IF NOT EXISTS public.users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    company     TEXT,
    plan        TEXT NOT NULL DEFAULT 'free',  -- free | pro | team | enterprise
    api_key     TEXT UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Usage table (audit counts per user per month)
CREATE TABLE IF NOT EXISTS public.usage (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    month          TEXT NOT NULL,              -- e.g. '2026-06'
    audit_count    INTEGER NOT NULL DEFAULT 0,
    last_audit_at  TIMESTAMPTZ,
    UNIQUE (user_id, month)
);

-- Row-level security: users can only read their own rows
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own row" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can read own usage" ON public.usage
    FOR SELECT USING (auth.uid() = user_id);

-- Service role bypasses RLS automatically — no extra policy needed for server-side writes.
