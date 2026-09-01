-- =====================================================================
-- 1. OVĚŘENÍ HESLA (Centrální funkce)
-- =====================================================================
-- Nahraď 'TvojeHesloAdmin' tvým skutečným heslem pro vstup do administrace.
-- Všechny ostatní funkce se pak budou řídit tímto jedním heslem.
CREATE OR REPLACE FUNCTION verify_admin_password(admin_password text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN admin_password = 'nigga123';
END;
$$;

-- =====================================================================
-- 2. FUNKCE 1: KONTAKTNÍ ZPRÁVY (INBOX)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.contact_messages (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL CHECK (char_length(name) <= 100),
  email text NOT NULL CHECK (char_length(email) <= 150),
  message text NOT NULL CHECK (char_length(message) <= 2000),
  resolved boolean DEFAULT false NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.contact_messages ENABLE ROW LEVEL SECURITY;

-- Kdokoliv může poslat zprávu přes kontaktní formulář
DROP POLICY IF EXISTS "Umožnit odesílání kontaktů komukoliv" ON public.contact_messages;
CREATE POLICY "Umožnit odesílání kontaktů komukoliv" ON public.contact_messages 
  FOR INSERT WITH CHECK (true);

-- Čtení a úpravy zpráv jsou zakázány zvenčí (řídí se zabezpečeným RPC na pozadí)
DROP POLICY IF EXISTS "Zamezit přímému přístupu ke zprávám" ON public.contact_messages;
CREATE POLICY "Zamezit přímému přístupu ke zprávám" ON public.contact_messages 
  FOR ALL USING (false);

-- RPC: Načtení zpráv pro administrátora
DROP FUNCTION IF EXISTS get_contact_messages_admin(text);
CREATE OR REPLACE FUNCTION get_contact_messages_admin(admin_password text)
RETURNS TABLE (
  id uuid,
  name text,
  email text,
  message text,
  resolved boolean,
  created_at timestamp with time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  RETURN QUERY SELECT m.id, m.name, m.email, m.message, m.resolved, m.created_at 
               FROM public.contact_messages m 
               ORDER BY m.resolved ASC, m.created_at DESC;
END;
$$;

-- RPC: Označení zprávy za vyřízenou
CREATE OR REPLACE FUNCTION resolve_contact_message_admin(admin_password text, message_id uuid, set_resolved boolean)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  UPDATE public.contact_messages 
  SET resolved = set_resolved 
  WHERE public.contact_messages.id = message_id;
END;
$$;

-- RPC: Smazání zprávy
CREATE OR REPLACE FUNCTION delete_contact_message_admin(admin_password text, message_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  DELETE FROM public.contact_messages 
  WHERE public.contact_messages.id = message_id;
END;
$$;

-- =====================================================================
-- 3. FUNKCE 2: STATISTIKY ZOBRAZENÍ (PAGE VIEWS)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.page_views (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id bigint,
  page_path text NOT NULL CHECK (char_length(page_path) <= 250),
  referrer text CHECK (char_length(referrer) <= 500),
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;

-- Kdokoli může zaslat event zobrazení stránky
DROP POLICY IF EXISTS "Umožnit logování zobrazení všem" ON public.page_views;
CREATE POLICY "Umožnit logování zobrazení všem" ON public.page_views 
  FOR INSERT WITH CHECK (true);

-- Čtení zvenčí zakázáno
DROP POLICY IF EXISTS "Zamezit přímému přístupu k zobrazením" ON public.page_views;
CREATE POLICY "Zamezit přímému přístupu k zobrazením" ON public.page_views 
  FOR SELECT USING (false);

-- RPC: Načtení všech zobrazení pro statistiky administrátora
DROP FUNCTION IF EXISTS get_page_views_admin(text);
CREATE OR REPLACE FUNCTION get_page_views_admin(admin_password text)
RETURNS TABLE (
  id uuid,
  project_id bigint,
  page_path text,
  referrer text,
  created_at timestamp with time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  RETURN QUERY SELECT v.id, v.project_id, v.page_path, v.referrer, v.created_at 
               FROM public.page_views v 
               ORDER BY v.created_at DESC;
END;
$$;

-- =====================================================================
-- 4. FUNKCE 3: OBSAH WEBU (CMS LIGHT)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.site_settings (
  key text PRIMARY KEY,
  value text NOT NULL,
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.site_settings ENABLE ROW LEVEL SECURITY;

-- Čtení je veřejné (web si musí načíst texty při startu)
DROP POLICY IF EXISTS "Veřejné čtení obsahu" ON public.site_settings;
CREATE POLICY "Veřejné čtení obsahu" ON public.site_settings 
  FOR SELECT USING (true);

-- Přímé zápisy zvenčí zakázány
DROP POLICY IF EXISTS "Zamezit přímému zápisu obsahu" ON public.site_settings;
CREATE POLICY "Zamezit přímému zápisu obsahu" ON public.site_settings 
  FOR ALL USING (false);

-- RPC: Zrušení / změna nastavení obsahu
CREATE OR REPLACE FUNCTION set_site_setting_admin(admin_password text, setting_key text, setting_value text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  INSERT INTO public.site_settings (key, value, updated_at)
  VALUES (setting_key, setting_value, now())
  ON CONFLICT (key) 
  DO UPDATE SET value = setting_value, updated_at = now();
END;
$$;

-- Vložení výchozích textů (pokud ještě neexistují)
INSERT INTO public.site_settings (key, value) VALUES
  ('maintenance_mode', 'false'),
  ('maintenance_message', 'Na webu právě probíhají plánované úpravy a aktualizace. Vracíme se již brzy!'),
  ('home_intro', 'Kameraman, fotograf a student filmové tvorby.'),
  ('about_sidebar_intro', 'Kameraman, fotograf a student filmové tvorby. Ve své práci se úzce specializuji na cinematografii a poutavý vizuální storytelling.'),
  ('about_bio', 'Studium na Slezské univerzitě v Opavě – Multimédia a popularizace.\n\nVysokoškolské studium propojující audiovizuální praxi s širším teoretickým přesahem. Zaměření na tvorbu komplexních multimediálních projektů, vizuální komunikaci a efektivní předávání příběhů.'),
  ('contact_email', 'levinskyj.cine@gmail.com'),
  ('instagram_link', 'https://www.instagram.com/levinskyj.cine/'),
  ('youtube_link', 'https://www.youtube.com/@LevinskyJ')
ON CONFLICT (key) DO NOTHING;

-- =====================================================================
-- 5. FUNKCE 4: NEWSLETTER (ODBĚRATELÉ)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.subscribers (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  email text UNIQUE NOT NULL CHECK (char_length(email) <= 150),
  unsubscribe_token text UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.subscribers ENABLE ROW LEVEL SECURITY;

-- Kdokoli se může přihlásit k newsletteru
DROP POLICY IF EXISTS "Veřejné přihlášení k odběru" ON public.subscribers;
CREATE POLICY "Veřejné přihlášení k odběru" ON public.subscribers 
  FOR INSERT WITH CHECK (true);

-- Čtení zvenčí zakázáno
DROP POLICY IF EXISTS "Zamezit přímému přístupu k odběratelům" ON public.subscribers;
CREATE POLICY "Zamezit přímému přístupu k odběratelům" ON public.subscribers 
  FOR SELECT USING (false);

-- RPC: Získání seznamu odběratelů
DROP FUNCTION IF EXISTS get_subscribers_admin(text);
CREATE OR REPLACE FUNCTION get_subscribers_admin(admin_password text)
RETURNS TABLE (
  id uuid,
  email text,
  unsubscribe_token text,
  created_at timestamp with time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  RETURN QUERY SELECT s.id, s.email, s.unsubscribe_token, s.created_at 
               FROM public.subscribers s 
               ORDER BY s.created_at DESC;
END;
$$;

-- RPC: Smazání odběratele ze seznamu
CREATE OR REPLACE FUNCTION delete_subscriber_admin(admin_password text, subscriber_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  DELETE FROM public.subscribers 
  WHERE public.subscribers.id = subscriber_id;
END;
$$;

-- RPC: Veřejné odhlášení z newsletteru pomocí tokenu
DROP FUNCTION IF EXISTS unsubscribe_by_token(text);
CREATE OR REPLACE FUNCTION unsubscribe_by_token(token text)
RETURNS TABLE (
  success boolean,
  message text
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  found_count integer;
BEGIN
  DELETE FROM public.subscribers 
  WHERE unsubscribe_token = token;
  
  GET DIAGNOSTICS found_count = ROW_COUNT;
  
  IF found_count > 0 THEN
    RETURN QUERY SELECT true, 'Byl jsi úspěšně odhlášen z newsletteru.'::text;
  ELSE
    RETURN QUERY SELECT false, 'Neplatný nebo expirovaný odkaz.'::text;
  END IF;
END;
$$;

-- RPC: Získání unsubscribe tokenu pro email (pro generování odkazů v emailech)
CREATE OR REPLACE FUNCTION get_subscriber_token_admin(admin_password text, subscriber_email text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  token text;
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  SELECT unsubscribe_token INTO token
  FROM public.subscribers 
  WHERE email = subscriber_email;
  
  RETURN token;
END;
$$;

-- =====================================================================
-- 6. FUNKCE 5: LIKES PRO JEDNOTLIVÁ MÉDIA (FOTKY/VIDEA)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.project_likes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id text NOT NULL CHECK (char_length(project_id) <= 100),
  media_src text NOT NULL CHECK (char_length(media_src) <= 500),
  user_fingerprint text NOT NULL CHECK (char_length(user_fingerprint) <= 200),
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(project_id, media_src, user_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_project_likes_project_id ON public.project_likes(project_id);
CREATE INDEX IF NOT EXISTS idx_project_likes_media_src ON public.project_likes(media_src);
CREATE INDEX IF NOT EXISTS idx_project_likes_fingerprint ON public.project_likes(user_fingerprint);

ALTER TABLE public.project_likes ENABLE ROW LEVEL SECURITY;

-- Kdokoli může číst počty liků
DROP POLICY IF EXISTS "Veřejné čtení liků" ON public.project_likes;
CREATE POLICY "Veřejné čtení liků" ON public.project_likes 
  FOR SELECT USING (true);

-- Kdokoli může přidat lajk (INSERT)
DROP POLICY IF EXISTS "Veřejné přidání lajku" ON public.project_likes;
CREATE POLICY "Veřejné přidání lajku" ON public.project_likes 
  FOR INSERT WITH CHECK (true);

-- Kdokoli může odstranit svůj vlastní lajk (DELETE)
DROP POLICY IF EXISTS "Veřejné odstranění vlastního lajku" ON public.project_likes;
CREATE POLICY "Veřejné odstranění vlastního lajku" ON public.project_likes 
  FOR DELETE USING (true);

-- RPC: Získat počet liků pro konkrétní médium
DROP FUNCTION IF EXISTS get_media_likes_count(text, text);
CREATE OR REPLACE FUNCTION get_media_likes_count(p_project_id text, p_media_src text)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  like_count bigint;
  clean_src text;
  fn text;
BEGIN
  clean_src := replace(p_media_src, '%25', '%');
  fn := split_part(clean_src, '/', -1);

  SELECT COUNT(*) INTO like_count
  FROM public.project_likes
  WHERE project_id = p_project_id 
    AND (
      media_src = p_media_src 
      OR media_src = clean_src
      OR replace(media_src, '%25', '%') = clean_src
      OR (fn != '' AND media_src LIKE '%' || fn)
    );
  
  RETURN like_count;
END;
$$;

-- RPC: Zjistit, zda uživatel dal médiu lajk
DROP FUNCTION IF EXISTS check_user_liked_media(text, text, text);
CREATE OR REPLACE FUNCTION check_user_liked_media(p_project_id text, p_media_src text, p_user_fingerprint text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  liked boolean;
  clean_src text;
  fn text;
BEGIN
  clean_src := replace(p_media_src, '%25', '%');
  fn := split_part(clean_src, '/', -1);

  SELECT EXISTS(
    SELECT 1 FROM public.project_likes
    WHERE project_id = p_project_id 
      AND user_fingerprint = p_user_fingerprint
      AND (
        media_src = p_media_src 
        OR media_src = clean_src
        OR replace(media_src, '%25', '%') = clean_src
        OR (fn != '' AND media_src LIKE '%' || fn)
      )
  ) INTO liked;
  
  RETURN liked;
END;
$$;

-- RPC: Přepnout stav lajku pro médium (toggle like)
DROP FUNCTION IF EXISTS toggle_media_like(text, text, text);
CREATE OR REPLACE FUNCTION toggle_media_like(p_project_id text, p_media_src text, p_user_fingerprint text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  existing_like uuid;
  new_count bigint;
  is_liked boolean;
  clean_src text;
  fn text;
BEGIN
  clean_src := replace(p_media_src, '%25', '%');
  fn := split_part(clean_src, '/', -1);

  -- Zjistit, zda lajk existuje
  SELECT id INTO existing_like
  FROM public.project_likes
  WHERE project_id = p_project_id 
    AND user_fingerprint = p_user_fingerprint
    AND (
      media_src = p_media_src 
      OR media_src = clean_src
      OR replace(media_src, '%25', '%') = clean_src
      OR (fn != '' AND media_src LIKE '%' || fn)
    );
  
  IF existing_like IS NOT NULL THEN
    -- Lajk existuje, odstraníme ho
    DELETE FROM public.project_likes WHERE id = existing_like;
    is_liked := false;
  ELSE
    -- Lajk neexistuje, přidáme ho
    INSERT INTO public.project_likes (project_id, media_src, user_fingerprint)
    VALUES (p_project_id, p_media_src, p_user_fingerprint);
    is_liked := true;
  END IF;
  
  -- Spočítat nový počet liků pro toto médium
  SELECT COUNT(*) INTO new_count
  FROM public.project_likes
  WHERE project_id = p_project_id 
    AND (
      media_src = p_media_src 
      OR media_src = clean_src
      OR replace(media_src, '%25', '%') = clean_src
      OR (fn != '' AND media_src LIKE '%' || fn)
    );
  
  RETURN jsonb_build_object(
    'liked', is_liked,
    'count', new_count
  );
END;
$$;

-- RPC: Admin funkce pro získání všech liků
DROP FUNCTION IF EXISTS get_all_likes_admin(text);
CREATE OR REPLACE FUNCTION get_all_likes_admin(admin_password text)
RETURNS TABLE (
  id uuid,
  project_id text,
  media_src text,
  user_fingerprint text,
  created_at timestamp with time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  RETURN QUERY 
  SELECT l.id, l.project_id, l.media_src, l.user_fingerprint, l.created_at 
  FROM public.project_likes l 
  ORDER BY l.created_at DESC;
END;
$$;

-- RPC: Admin funkce pro smazání konkrétního lajku
CREATE OR REPLACE FUNCTION delete_like_admin(admin_password text, like_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  DELETE FROM public.project_likes 
  WHERE public.project_likes.id = like_id;
END;
$$;
