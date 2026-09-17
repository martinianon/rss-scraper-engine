import sys
from xml.sax.saxutils import escape
import requests
from bs4 import BeautifulSoup

# URL del sitio que queremos escanear
TARGET_URL = "https://ministeriopublico.jusrionegro.gov.ar/comunicacion.php"
OUTPUT_FILE = "feed.xml"

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text
    except Exception as e:
        print(f"Error al descargar la página: {e}")
        sys.exit(1)

def parse_articles(html):
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Buscamos las cajas de noticias en el HTML del sitio
    boxes = soup.select("div.col-md-9.well.well-sm")

    for box in boxes:
        # Extraer Título y Enlace
        a_tag = box.select_one("h3 a") or box.select_one("a")
        if not a_tag:
            continue
        
        title = a_tag.get_text(strip=True)
        link = a_tag.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://ministeriopublico.jusrionegro.gov.ar/{link.lstrip('/')}"

        # Extraer Fecha
        small_tag = box.select_one("small")
        pub_date = small_tag.get_text(strip=True) if small_tag else ""

        # Extraer Imagen
        img_tag = box.select_one("img")
        img_url = ""
        if img_tag and img_tag.get("src"):
            img_src = img_tag.get("src")
            img_url = img_src if img_src.startswith("http") else f"https://ministeriopublico.jusrionegro.gov.ar/{img_src.lstrip('/')}"

        # Extraer Texto
        p_tags = box.select("p")
        description_text = " ".join([p.get_text(strip=True) for p in p_tags])

        # Armar el contenido combinando imagen y texto
        content_html = ""
        if img_url:
            content_html += f'<img src="{img_url}" /><br/>'
        content_html += description_text

        articles.append({
            "title": title,
            "link": link,
            "date": pub_date,
            "description": content_html,
            "guid": link
        })

    return articles

def generate_rss_xml(articles):
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
  <title>Ministerio Público de Río Negro - Novedades</title>
  <link>{TARGET_URL}</link>
  <description>Feed RSS automatizado</description>
  <language>es-ar</language>
{items_str}
</channel>
</rss>"""

def main():
    print("Iniciando la lectura del sitio oficial...")
    html = fetch_html(TARGET_URL)
    articles = parse_articles(html)
    print(f"Noticias encontradas: {len(articles)}")

    if articles:
        rss_xml = generate_rss_xml(articles)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print(f"Archivo {OUTPUT_FILE} generado exitosamente.")
    else:
        print("No se encontraron noticias para generar el feed.")

if __name__ == "__main__":
    main()
