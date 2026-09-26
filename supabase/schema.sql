-- Bé Vào Lớp 1 — cơ sở dữ liệu Supabase
-- Mỗi gia đình đăng nhập bằng một tài khoản (Supabase Auth). Mọi bảng đều bật Row Level Security:
-- tài khoản nào chỉ đọc/ghi được dữ liệu của chính mình.
-- Cách chạy: Supabase Dashboard → SQL Editor → dán toàn bộ file này → Run. Chạy lại nhiều lần vẫn an toàn.

-- Các bé trong gia đình
create table if not exists public.children (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  id         text        not null,
  name       text        not null,
  avatar     text        not null default '🐯',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted    boolean     not null default false,
  primary key (user_id, id)
);

-- Tiến trình của từng bé: màn đã qua, số sao, sức mạnh, cài đặt (một dòng JSON mỗi bé)
create table if not exists public.progress (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  child_id   text        not null,
  state      jsonb       not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, child_id),
  foreign key (user_id, child_id) references public.children (user_id, id) on delete cascade
);

-- Lịch sử: mỗi buổi học (một màn chơi hoặc một bài luyện) là một dòng
create table if not exists public.sessions (
  user_id  uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  child_id text        not null,
  id       text        not null,
  at       timestamptz not null,
  kind     text        not null default '',
  title    text        not null default '',
  data     jsonb       not null default '{}'::jsonb,
  primary key (user_id, id),
  foreign key (user_id, child_id) references public.children (user_id, id) on delete cascade
);
create index if not exists sessions_child_at_idx on public.sessions (user_id, child_id, at);

-- Thống kê đúng/sai theo từng chữ, tiếng, dạng toán. Mỗi máy giữ bộ đếm riêng (device_id),
-- app cộng các máy lại khi hiển thị, nên hai máy học cùng lúc không ghi đè số của nhau.
create table if not exists public.item_stats (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  child_id   text        not null,
  device_id  text        not null,
  item_key   text        not null,
  label      text        not null default '',
  cat        text        not null default '',
  ok         integer     not null default 0 check (ok >= 0),
  miss       integer     not null default 0 check (miss >= 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, child_id, device_id, item_key),
  foreign key (user_id, child_id) references public.children (user_id, id) on delete cascade
);

alter table public.children   enable row level security;
alter table public.progress   enable row level security;
alter table public.sessions   enable row level security;
alter table public.item_stats enable row level security;

do $$
declare t text;
begin
  foreach t in array array['children', 'progress', 'sessions', 'item_stats'] loop
    execute format('drop policy if exists "own rows" on public.%I', t);
    execute format('create policy "own rows" on public.%I for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id)', t);
  end loop;
end $$;

grant select, insert, update, delete on public.children, public.progress, public.sessions, public.item_stats to authenticated;
revoke all on public.children, public.progress, public.sessions, public.item_stats from anon;
