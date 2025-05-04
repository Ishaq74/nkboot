from urllib.parse import urlparse
import streamlit as st
import requests
from bs4 import BeautifulSoup
from bs4.exceptions import FeatureNotFound
from serpapi import GoogleSearch
from urllib.robotparser import RobotFileParser
from dotenv import load_dotenv
import os
import csv
import json

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    st.error("Clé API SerpApi manquante.")
    st.stop()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

EXCLUDED_DOMAINS = [
    "amazon.com", "youtube.com", "tiktok.com", "facebook.com", "forum", "wikipedia.org", "twitter.com",
    "instagram.com", "linkedin.com", "pinterest.com", "tripadvisor.com", "yelp.com", "play.google.com", "apple.com",
    "microsoft.com", "github.com", "stackoverflow.com", "reddit.com", "quora.com", "medium.com", "blogspot.com", "walmart.com",
    "ebay.com", "etsy.com", "craigslist.org", "webmd.com", "healthline.com", "mayoclinic.org", "medicalnewstoday.com", "planity.com",
]

EXCLUDED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.pdf']
EXCLUDED_PATHS = ['/wp-content/', '/uploads/', '/assets/', '/images/', '/media/', '/static/', '/cache/']

def save_to_csv(filename, data):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow([row])

def save_to_json(filename, data):
    with open(filename, mode='w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def load_from_json(filename):
    if os.path.exists(filename):
        with open(filename, mode='r', encoding='utf-8') as file:
            return json.load(file)
    return None

def load_from_csv(filename):
    if os.path.exists(filename):
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            return [row[0] for row in reader if row]
    return []

def is_excluded_url(url):
    url_lower = url.lower()
    domain = urlparse(url).netloc.lower()
    if any(excluded in domain for excluded in EXCLUDED_DOMAINS):
        st.warning(f"URL exclue (domaine exclu) : {url}")
        return True
    if any(url_lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        st.warning(f"URL exclue (extension fichier) : {url}")
        return True
    if any(path in url_lower for path in EXCLUDED_PATHS):
        st.warning(f"URL exclue (chemin exclu) : {url}")
        return True
    return False

def get_sitemap_from_robots(url):
    if is_excluded_url(url):
        return []

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = f"{base_url}/robots.txt"
    st.info(f"Tentative de récupération du robots.txt : {robots_url}")

    try:
        response = requests.get(robots_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        rp = RobotFileParser()
        rp.parse(response.text.splitlines())
        sitemaps = rp.site_maps() or []
        st.info(f"Sitemaps trouvés dans robots.txt : {sitemaps}")

        if not sitemaps:
            st.warning(f"Aucun sitemap dans {robots_url}. Tentative avec sitemap par défaut.")
            default_sitemap = f"{base_url}/sitemap.xml"
            if not is_excluded_url(default_sitemap):
                try:
                    response = requests.get(default_sitemap, headers=HEADERS, timeout=10)
                    response.raise_for_status()
                    sitemaps = [default_sitemap]
                    st.success(f"Sitemap par défaut trouvé : {default_sitemap}")
                except requests.RequestException:
                    st.warning(f"Le sitemap par défaut {default_sitemap} est inaccessible.")
        filtered_sitemaps = [s for s in sitemaps if not is_excluded_url(s)]
        st.info(f"Sitemaps après filtrage : {filtered_sitemaps}")
        save_to_csv("sitemaps.csv", filtered_sitemaps)
        return filtered_sitemaps
    except requests.RequestException as e:
        st.warning(f"Erreur lors de la récupération de {robots_url} : {e}")
        default_sitemap = f"{base_url}/sitemap.xml"
        if not is_excluded_url(default_sitemap):
            try:
                response = requests.get(default_sitemap, headers=HEADERS, timeout=10)
                response.raise_for_status()
                st.success(f"Sitemap par défaut trouvé : {default_sitemap}")
                save_to_csv("sitemaps.csv", [default_sitemap])
                return [default_sitemap]
            except requests.RequestException:
                st.warning(f"Échec de la récupération du sitemap par défaut {default_sitemap} : {e}")
        return []

def get_all_sitemaps(url, visited=None, depth=0, max_depth=5):
    if visited is None:
        visited = set()

    st.info(f"Traitement de l'URL : {url} (profondeur : {depth})")

    if depth > max_depth:
        st.warning(f"Profondeur maximale atteinte pour {url} : {depth} > {max_depth}")
        return []
    if url in visited:
        st.warning(f"URL déjà visitée : {url}")
        return []
    if is_excluded_url(url):
        return []

    visited.add(url)
    all_page_urls = []

    try:
        st.info(f"Tentative de récupération : {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        st.info(f"Contenu brut de {url} (extrait) : {response.text[:500]}...")

        try:
            soup = BeautifulSoup(response.text, "xml")
        except FeatureNotFound:
            st.warning("Parseur XML 'lxml' non installé. Utilisation de 'html.parser'.")
            soup = BeautifulSoup(response.text, "html.parser")

        locs = [loc.text.strip() for loc in soup.find_all("loc") if loc.text]
        st.success(f"Récupéré : {url} ({len(locs)} URLs trouvées)")
        st.info(f"URLs trouvées dans {url} : {locs}")

        for loc in locs:
            if "sitemap" in loc.lower():
                st.info(f"Sous-sitemap détecté : {loc}")
                sub_urls = get_all_sitemaps(loc, visited, depth + 1, max_depth)
                all_page_urls.extend(sub_urls)
                st.info(f"Ajout de {len(sub_urls)} URLs depuis le sous-sitemap {loc}")
            elif not is_excluded_url(loc):
                all_page_urls.append(loc)
                st.info(f"Page ajoutée : {loc}")
            else:
                st.warning(f"URL filtrée : {loc}")
    except requests.RequestException as e:
        st.warning(f"Échec de la récupération de {url} : {e}")

    st.info(f"Total URLs collectées pour {url} : {len(all_page_urls)}")
    save_to_csv("urls_sitemap.csv", all_page_urls)
    return all_page_urls

def fetch_page_content(url):
    if is_excluded_url(url):
        return "URL exclue"
    st.info(f"Récupération du contenu : {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup.find_all(['header', 'footer', 'nav']):
            tag.decompose()
        content = soup.get_text(separator="\n").strip()
        st.info(f"Contenu extrait de {url} : {content[:100]}...")
        return content if content else "Contenu vide."
    except requests.RequestException as e:
        st.warning(f"Erreur lors de la récupération du contenu de {url} : {e}")
        return f"Erreur : {e}"

def get_serpapi_results(keyword):
    st.info(f"Lancement de la recherche SERP pour : {keyword}")
    try:
        account_response = requests.get(f"https://serpapi.com/account?api_key={SERPAPI_API_KEY}")
        if account_response.ok:
            account_data = account_response.json()
            credits = account_data.get("total_searches_left")
            if credits is not None:
                st.info(f"Crédits SerpAPI restants (compte) : {credits}")
                if credits <= 5:
                    st.warning(f"⚠️ Attention : Il ne reste que {credits} crédits SerpAPI.")

        search_params = {
            "q": keyword,
            "api_key": SERPAPI_API_KEY,
            "num": 10
        }
        search = GoogleSearch(search_params)
        results = search.get_dict()

        urls = [result["link"] for result in results.get("organic_results", [])[:10]]
        filtered_urls = [url for url in urls if not is_excluded_url(url)]
        st.info(f"Résultats SERP pour '{keyword}' après filtrage : {filtered_urls}")
        save_to_json("serpapi_results.json", filtered_urls)
        return filtered_urls
    except Exception as e:
        st.error(f"Erreur SerpAPI : {e}")
        return []
