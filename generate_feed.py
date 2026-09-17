import sys
import os
from xml.sax.saxutils import escape
import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIGURACIÓN DE SITIOS A SCRAPEAR
# Para agregar un nuevo sitio, simplemente añade una entrada a este listado.
# ==============================================================================
SITES_CONFIG = [
    {
        "id": "ministerio_publico",
        "name": "Ministerio Público de Río Negro",
        "url": "https://ministeriopublico.jusrionegro.gov.ar/comunicacion.php",
        "output_file": "feed.xml",
        "container_selector": "div.col-md-9.well.well-sm, div.well",
        "title_selector": "h3 a, a",
        "date_selector": "small",
        "img_selector": "img",
        "text_selector": "p",
        "base_url": "https://ministeriopublico.jusrionegro.gov.ar/"
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text
    except Exception as e:
        print(f"  [ERROR] Fallo al descargar {url}: {e}")
        return None

def parse_site(site, html):
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    boxes = soup.select(site["container_selector"])

    for box in boxes:
        a_tag = box.select_one(site["title_selector"])
        if not a_tag:
            continue
        
        title = a_tag.get_text(strip=True)
        link = a_tag.get("href", "")
        if link and not link.startswith("http"):
            link = f"{site['base_url'].rstrip('/')}/{link.lstrip('/')}"

        small_tag = box.select_one(site["date_selector"]) if site.get("date_selector") else None
        pub_date = small_tag.get_text(strip=True) if small_tag else ""

        img_tag = box.select_one(site["img_selector"]) if site.get("img_selector") else None
        img_url = ""
        if img_tag and img_tag.get("src"):
            src = img_tag.get("src")
            img_url = src if src.startswith("http") else f"{site['base_url'].rstrip('/')}/{src.lstrip('/')}"

        p_tags = box.select(site["text_selector"]) if site.get("text_selector") else []
        description_text = " ".join([p.get_text(strip=True) for p in p_tags])

        content_html = f'<img src="{img_url}" /><br/>' if img_url else ""
        content_html += description_text

        articles.append({
            "title": title,
            "link": link,
            "date": pub_date,
            "description": content_html,
            "guid": link
        })
    return articles

def generate_rss_xml(site, articles):
    xml_items = []
    for item in articles:
        xml_item = f"""    <item>
      <title>{escape(item['title'])}</title>
      <link>{escape(item['link'])}</link>
      <description>{escape(item['description'])}</description>
      <guid isPermaLink="true">{escape(item['guid'])}</guid>
    </item>"""
        xml_items.append(xml_item)

    items_str = "\n".join(xml_items)
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{escape(site['name'])}</title>
  <link>{site['url']}</link>
  <description>Feed RSS automatizado para {escape(site['name'])}</description>
  <language>es-ar</language>
{items_str}
</channel>
</rss>"""

def main():
    print("=== INICIANDO MOTOR GENERADOR CENTRALIZADO DE FEEDS ===")
    for site in SITES_CONFIG:
        print(f"\nProcesando: {site['name']} ({site['url']})")
        html = fetch_html(site['url'])
        articles = parse_site(site, html) if html else []
        print(f"  -> Noticias encontradas: {len(articles)}")

        rss_xml = generate_rss_xml(site, articles)
        with open(site['output_file'], "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print(f"  -> Archivo guardado/actualizado: {site['output_file']}")

if __name__ == "__main__":
    main()
