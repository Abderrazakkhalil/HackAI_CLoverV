-- Hirfati / HackAI initial schema
-- Run in Supabase Dashboard → SQL Editor.
--
-- Tables:
--   profiles  — extends auth.users with artisan metadata
--   listings  — marketplace listings (mirrors the Product Pydantic schema)
--
-- The backend uses the service-role key and bypasses RLS, but policies are
-- defined as a safety net for any future direct-from-client access.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- profiles
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  id              uuid primary key references auth.users(id) on delete cascade,
  full_name       text not null default '',
  city_region     text not null default '',
  phone           text not null default '',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- enums (use DO blocks so the migration is idempotent)
-- ---------------------------------------------------------------------------
do $$ begin
  create type listing_status as enum ('draft','published','sold','archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type price_source_t as enum ('user','extracted','ai_recommended');
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------------
-- listings
-- ---------------------------------------------------------------------------
create table if not exists public.listings (
  id                      uuid primary key default gen_random_uuid(),
  seller_id               uuid not null references auth.users(id) on delete cascade,
  status                  listing_status not null default 'published',

  -- localized text
  title_en                text not null default '',
  title_fr                text not null default '',
  title_ar                text not null default '',
  description_en          text not null default '',
  description_fr          text not null default '',
  description_ar          text not null default '',

  -- taxonomy
  category                text not null default 'Handmade',
  subcategory             text,
  tags                    text[] not null default '{}',
  materials               text[] not null default '{}',
  colors                  text[] not null default '{}',
  images                  text[] not null default '{}',

  -- pricing
  price_amount            numeric(10,2) not null default 0,
  price_currency          text not null default 'MAD',
  price_usd_estimate      numeric(10,2) not null default 0,
  price_negotiable        boolean not null default true,
  price_source            price_source_t not null default 'user',

  -- structured fields (JSONB so the schema can evolve)
  dimensions              jsonb not null default '{}'::jsonb,
  origin                  jsonb not null default '{}'::jsonb,
  shipping                jsonb not null default '{}'::jsonb,

  -- product details
  condition               text not null default 'handmade-new',
  quantity_available      int,
  lead_time_days          int,
  artisan_notes           text,
  raw_transcript          text not null default '',

  -- seeding key (lets seed script upsert idempotently)
  seed_key                text unique,

  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- indexes
-- ---------------------------------------------------------------------------
create index if not exists listings_category_idx  on public.listings (category);
create index if not exists listings_status_idx    on public.listings (status);
create index if not exists listings_seller_idx    on public.listings (seller_id);
create index if not exists listings_materials_gin on public.listings using gin (materials);
create index if not exists listings_colors_gin    on public.listings using gin (colors);
create index if not exists listings_tags_gin      on public.listings using gin (tags);

-- ---------------------------------------------------------------------------
-- updated_at triggers
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_profiles_updated on public.profiles;
create trigger trg_profiles_updated
  before update on public.profiles
  for each row execute function public.set_updated_at();

drop trigger if exists trg_listings_updated on public.listings;
create trigger trg_listings_updated
  before update on public.listings
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.listings enable row level security;

-- profiles: each user can read/write only their own row
drop policy if exists "profiles self read"   on public.profiles;
drop policy if exists "profiles self insert" on public.profiles;
drop policy if exists "profiles self update" on public.profiles;
create policy "profiles self read"   on public.profiles for select using (auth.uid() = id);
create policy "profiles self insert" on public.profiles for insert with check (auth.uid() = id);
create policy "profiles self update" on public.profiles for update using (auth.uid() = id);

-- listings: anyone can read published listings; sellers manage their own
drop policy if exists "listings public read" on public.listings;
drop policy if exists "listings owner all"   on public.listings;
create policy "listings public read" on public.listings for select using (status = 'published');
create policy "listings owner all"   on public.listings for all
  using (auth.uid() = seller_id)
  with check (auth.uid() = seller_id);
