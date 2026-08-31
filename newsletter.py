#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
newsletter.py — Send email updates to newsletter subscribers using SMTP
======================================================================
"""

import os
import sys
import json
import smtplib
import ssl
import time
import urllib.request
import urllib.parse
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CONFIG_FILE = Path(__file__).parent / "newsletter_config.json"
PROJECTS_FILE = Path(__file__).parent / "projects.json"
SENT_ID_FILE = Path(__file__).parent / "last_sent_project_id.txt"
LOG_FILE = Path(__file__).parent / "newsletter.log"

SUPABASE_URL = "https://jmxpqcsywnlbmfrylnhw.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpteHBxY3N5d25sYm1mcnlsbmh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODkwNjcsImV4cCI6MjEwMzc2NTA2N30.pFgifOtNk2tLGJLEYeughUByfT6um85kfO2r7OopEtA"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def ensure_config():
    if not CONFIG_FILE.exists():
        default_config = {
            "admin_password": "TvojeSkutecneHeslo",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 465,
            "email_sender": "levinskyj.cine@gmail.com",
            "email_password": "tvuj_app_password_pro_gmail",
            "site_url": "https://levinskyj.art"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        log("Vytvořena šablona newsletter_config.json. Nastavte prosím přihlašovací údaje.")
        return None
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        log(f"Chyba při načítání newsletter_config.json: {e}")
        return None

def get_latest_project():
    if not PROJECTS_FILE.exists():
        log("projects.json neexistuje.")
        return None
    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            projects = json.load(f)
        if not projects:
            log("V projects.json nejsou žádné projekty.")
            return None
        # Find the project with the highest ID or just the last in list
        return projects[-1]
    except Exception as e:
        log(f"Chyba při načítání projects.json: {e}")
        return None

def fetch_subscribers(admin_password):
    url = f"{SUPABASE_URL}/rest/v1/rpc/get_subscribers_admin"
    req_body = json.dumps({"admin_password": admin_password}).encode("utf-8")
    
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "NewsletterSender/1.0"
    }
    
    req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            emails = [row["email"] for row in data if "email" in row]
            return emails
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        log(f"Chyba při stahování odběratelů ze Supabase (HTTP {e.code}): {e.reason}")
        if error_body:
            log(f"Detail chyby ze Supabase: {error_body}")
        log("Ujistěte se prosím, že jste v Supabase SQL Editoru spustili celý skript 'supabase_setup.sql' a že heslo 'admin_password' v 'newsletter_config.json' odpovídá heslu v DB.")
        return []
    except Exception as e:
        log(f"Chyba při stahování odběratelů ze Supabase: {e}")
        return []

def send_email(config, recipient, project):
    sender = config.get("email_sender")
    site_url = config.get("site_url", "https://levinskyj.art").rstrip("/")
    
    title = project.get("title", "Nový projekt")
    year = project.get("year", "")
    bio = project.get("bio", "")
    project_id = project.get("id", "")
    
    # Build visual media gallery
    media_list = project.get("media", [])
    gallery_html = ""
    
    if media_list:
        gallery_items_html = []
        for item in media_list[:6]:
            kind = item.get("type", "photo")
            thumb_path = item.get("thumbnail") or item.get("src", "")
            if not thumb_path:
                continue
            
            thumb_url = thumb_path
            if not (thumb_url.startswith("http://") or thumb_url.startswith("https://") or thumb_url.startswith("data:")):
                thumb_url = f"{site_url}/{thumb_url.lstrip('/')}"
            
            item_title = item.get("title", "")
            escaped_title = item_title.replace('"', '&quot;').replace("'", "&#39;")
            
            project_link = f"{site_url}/project.html?id={project_id}"
            kind_label = "Video" if kind == "video" else "Foto"
            
            play_overlay = ""
            if kind == "video":
                play_overlay = f"""
                <div style="position: absolute; top:0; left:0; right:0; bottom:0; background-color: rgba(0,0,0,0.25); border-radius: 8px; display: block;">
                    <table role="presentation" border="0" cellspacing="0" cellpadding="0" style="width: 100%; height: 100%;">
                        <tr>
                            <td align="center" valign="middle" style="height: 110px; vertical-align: middle;">
                                <div style="width: 36px; height: 36px; line-height: 36px; border-radius: 18px; background-color: #ffffff; text-align: center; color: #1c1917; font-size: 13px; font-weight: bold; border: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.25); display: inline-block;">&#9654;</div>
                            </td>
                        </tr>
                    </table>
                </div>
                """
            
            item_html = f"""
            <!--[if mso]>
            <td align="left" valign="top" style="padding-right: 12px; width: 170px;">
            <![endif]-->
            <div style="display: inline-block; width: 170px; margin-right: 12px; vertical-align: top; white-space: normal; text-align: left;">
                <a href="{project_link}" style="text-decoration: none; display: block;">
                    <div style="position: relative; width: 170px; height: 110px; border-radius: 8px; overflow: hidden; border: 1px solid #e7e5e4; background-color: #1c1917;">
                        <img src="{thumb_url}" width="170" height="110" style="display: block; width: 170px; height: 110px; object-fit: cover; border-radius: 7px; border: 0;" alt="{escaped_title}" />
                        {play_overlay}
                    </div>
                    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; color: #78716c; margin-top: 6px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-left: 2px;">
                        <span style="text-transform: uppercase; color: #2c3e50; font-weight: 600;">{kind_label}</span> &middot; {escaped_title}
                    </div>
                </a>
            </div>
            <!--[if mso]>
            </td>
            <![endif]-->
            """
            gallery_items_html.append(item_html)
            
        if gallery_items_html:
            gallery_html = f"""
            <div style="margin: 24px 0 32px 0;">
                <h3 style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #78716c; margin: 0 0 12px 0; padding-left: 2px;">Galerie projektu</h3>
                <div style="width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 8px;">
                    <div style="white-space: nowrap; font-size: 0;">
                        <!--[if mso]>
                        <table role="presentation" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                        <![endif]-->
                        {"".join(gallery_items_html)}
                        <!--[if mso]>
                        </tr>
                        </table>
                        <![endif]-->
                    </div>
                </div>
            </div>
            """

    # HTML template matching the website's minimalist/Apple design
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #faf8f5;
                color: #1c1917;
                margin: 0;
                padding: 40px 20px;
                -webkit-font-smoothing: antialiased;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border: 1px solid #e7e5e4;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(28, 25, 23, 0.03);
            }}
            .header {{
                padding: 32px 32px 20px 32px;
                border-bottom: 1px solid #f5f5f4;
            }}
            .brand-name {{
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: #2c3e50;
                margin: 0 0 4px 0;
            }}
            .brand-role {{
                font-size: 11px;
                color: #78716c;
                margin: 0;
            }}
            .body {{
                padding: 32px;
            }}
            .meta {{
                font-size: 11px;
                font-weight: 500;
                color: #78716c;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 8px;
            }}
            .project-title {{
                font-size: 24px;
                font-weight: 700;
                color: #1c1917;
                margin: 0 0 16px 0;
                line-height: 1.25;
            }}
            .project-bio {{
                font-size: 14.5px;
                line-height: 1.6;
                color: #44403c;
                margin: 0 0 28px 0;
            }}
            .btn-container {{
                margin-bottom: 16px;
            }}
            .btn {{
                display: inline-block;
                background-color: #2c3e50;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.04em;
                transition: opacity 0.2s;
            }}
            .footer {{
                padding: 24px 32px;
                background-color: #faf8f5;
                border-top: 1px solid #f5f5f4;
                text-align: center;
            }}
            .footer p {{
                font-size: 11px;
                color: #78716c;
                margin: 4px 0;
                line-height: 1.5;
            }}
            .footer a {{
                color: #78716c;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="brand-name">Jan Levínský</h1>
                <p class="brand-role">Cinematography & Photography</p>
            </div>
            <div class="body">
                <div class="meta">Nový projekt / {year}</div>
                <h2 class="project-title">{title}</h2>
                <p class="project-bio">{bio}</p>
                {gallery_html}
                <div class="btn-container">
                    <a href="{site_url}/project.html?id={project_id}" class="btn" style="color: #ffffff;">Zobrazit projekt</a>
                </div>
            </div>
            <div class="footer">
                <p>© {time.strftime('%Y')} Jan Levínský. Všechna práva vyhrazena.</p>
                <p>Tento e-mail jste obdrželi, protože jste se přihlásili k odběru novinek na <a href="{site_url}">{site_url.replace('https://', '').replace('http://', '')}</a>.</p>
                <p>Pokud si již nepřejete dostávat tyto e-maily, napište prosím na <a href="mailto:{sender}">{sender}</a>.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Jan Levínský – Cinematography & Photography\n\nNový projekt ({year}): {title}\n\n{bio}\n\nOdkaz: {site_url}/project.html?id={project_id}"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Nový projekt: {title}"
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port", 465)
    smtp_password = config.get("email_password")
    
    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server_conn:
            server_conn.login(sender, smtp_password)
            server_conn.sendmail(sender, recipient, msg.as_string())
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server_conn:
            server_conn.ehlo()
            server_conn.starttls(context=context)
            server_conn.ehlo()
            server_conn.login(sender, smtp_password)
            server_conn.sendmail(sender, recipient, msg.as_string())

def main():
    log("Spouštím odesílání newsletteru...")
    config = ensure_config()
    if not config:
        log("Ukončuji - chybějící konfigurace.")
        sys.exit(0)
        
    latest_project = get_latest_project()
    if not latest_project:
        log("Ukončuji - nebyl nalezen žádný projekt v projects.json.")
        sys.exit(0)
        
    project_id = str(latest_project.get("id", ""))
    if not project_id:
        log("Ukončuji - poslední projekt nemá platné ID.")
        sys.exit(0)
        
    # Check if we already sent a newsletter for this project ID
    last_sent_id = ""
    if SENT_ID_FILE.exists():
        try:
            last_sent_id = SENT_ID_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
            
    if last_sent_id == project_id:
        log(f"Newsletter pro projekt s ID {project_id} ({latest_project.get('title')}) již byl odeslán. Přeskakuji.")
        sys.exit(0)
        
    # Check if default configs are still present
    if config.get("admin_password") == "TvojeSkutecneHeslo" or config.get("email_password") == "tvuj_app_password_pro_gmail":
        log("Ukončuji - v newsletter_config.json jsou stále defaultní hodnoty.")
        sys.exit(0)
        
    # Fetch subscribers
    emails = fetch_subscribers(config.get("admin_password"))
    if not emails:
        log("Nenalezeni žádní odběratelé k obeslání.")
        sys.exit(0)
        
    log(f"Nalezeno {len(emails)} odběratelů pro odeslání...")
    
    success_count = 0
    fail_count = 0
    
    for email in emails:
        try:
            send_email(config, email, latest_project)
            log(f"Odesláno odběrateli: {email}")
            success_count += 1
            time.sleep(0.5) # Sleep 500ms between emails to prevent spam filters / server blocks
        except Exception as e:
            log(f"Selhalo odeslání pro {email}: {e}")
            fail_count += 1
            
    log(f"Obeslání dokončeno. Úspěšně: {success_count}, Selhalo: {fail_count}")
    
    # Save the last sent ID
    if success_count > 0:
        try:
            SENT_ID_FILE.write_text(project_id, encoding="utf-8")
            log(f"Project ID {project_id} zapsán jako odeslaný.")
        except Exception as e:
            log(f"Chyba při zápisu odeslaného ID: {e}")

if __name__ == "__main__":
    main()
