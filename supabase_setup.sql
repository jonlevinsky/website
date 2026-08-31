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
  RETURN admin_password = 'TvojeHesloAdmin';
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
CREATE POLICY "Umožnit odesílání kontaktů komukoliv" ON public.contact_messages 
  FOR INSERT WITH CHECK (true);

-- Čtení a úpravy zpráv jsou zakázány zvenčí (řídí se zabezpečeným RPC na pozadí)
CREATE POLICY "Zamezit přímému přístupu ke zprávám" ON public.contact_messages 
  FOR ALL USING (false);

-- RPC: Načtení zpráv pro administrátora
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
CREATE POLICY "Umožnit logování zobrazení všem" ON public.page_views 
  FOR INSERT WITH CHECK (true);

-- Čtení zvenčí zakázáno
CREATE POLICY "Zamezit přímému přístupu k zobrazením" ON public.page_views 
  FOR SELECT USING (false);

-- RPC: Načtení všech zobrazení pro statistiky administrátora
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
CREATE POLICY "Veřejné čtení obsahu" ON public.site_settings 
  FOR SELECT USING (true);

-- Přímé zápisy zvenčí zakázány
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
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.subscribers ENABLE ROW LEVEL SECURITY;

-- Kdokoli se může přihlásit k newsletteru
CREATE POLICY "Veřejné přihlášení k odběru" ON public.subscribers 
  FOR INSERT WITH CHECK (true);

-- Čtení zvenčí zakázáno
CREATE POLICY "Zamezit přímému přístupu k odběratelům" ON public.subscribers 
  FOR SELECT USING (false);

-- RPC: Získání seznamu odběratelů
CREATE OR REPLACE FUNCTION get_subscribers_admin(admin_password text)
RETURNS TABLE (
  id uuid,
  email text,
  created_at timestamp with time zone
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT verify_admin_password(admin_password) THEN
    RAISE EXCEPTION 'Neplatné heslo.';
  END IF;

  RETURN QUERY SELECT s.id, s.email, s.created_at 
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
