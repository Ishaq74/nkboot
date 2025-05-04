import streamlit as st
import json
from utils import (
    get_serpapi_results,
    get_sitemap_from_robots,
    get_all_sitemaps,
    load_from_json,
    load_from_csv,
    save_to_json,
    save_to_csv,
    export_enriched_to_csv
)
from database import (
    store_structure_in_sqlite,
    store_enriched_pages_in_sqlite,
    store_serp_results,
    store_sitemap_urls,
    load_structure_from_db,
    load_sitemap_from_db,
    load_serp_from_db,
    load_enriched_from_db,
    export_sitemap_from_db,
    export_serp_from_db
)
from ai_processing import (
    generate_structure_with_ai,
    enrich_structure_to_table,
    generate_enriched_table_from_titles,
    test_api
)
from output import generate_markdown_table, generate_csv

st.title("Générateur de structure de site SEO")

selected_api = st.sidebar.selectbox("Choisir API", ["Gemini", "Anthropic", "Grok"])
if st.sidebar.button("Tester API"):
    test_api(selected_api)

st.sidebar.markdown("---")
st.sidebar.subheader("📁 Recharger depuis fichier")

if st.sidebar.button("Charger SERP JSON"):
    serp = load_from_json("serpapi_results.json")
    if serp:
        st.session_state["serp_urls"] = serp
        st.success("✅ SERP rechargé.")
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger URLs Sitemap"):
    sitemap_urls = load_from_csv("urls_sitemap.csv")
    if sitemap_urls:
        st.session_state["sitemap_urls"] = sitemap_urls
        st.success("✅ Sitemaps rechargés.")
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger Structure IA"):
    struct = load_from_json("structure_ia.json")
    if struct:
        st.session_state["structure"] = struct
        st.success("✅ Structure IA rechargée.")
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger Tableau enrichi"):
    enriched = load_from_json("enriched_table.json")
    if enriched:
        st.session_state["enriched"] = enriched
        st.success("✅ Tableau enrichi rechargé.")
    else:
        st.warning("❌ Fichier introuvable ou vide.")

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Export manuel")

if st.sidebar.button("Exporter SERP"):
    if st.session_state.get("serp_urls"):
        save_to_json("serpapi_results.json", st.session_state["serp_urls"])
        st.sidebar.success("✅ SERP exporté.")
    else:
        st.sidebar.warning("❌ Aucune donnée SERP à exporter.")

if st.sidebar.button("Exporter Sitemaps"):
    if st.session_state.get("sitemap_urls"):
        save_to_csv("urls_sitemap.csv", st.session_state["sitemap_urls"])
        st.sidebar.success("✅ Sitemaps exportés.")
    else:
        st.sidebar.warning("❌ Aucune URL sitemap à exporter.")

if st.sidebar.button("Exporter Structure"):
    if st.session_state.get("structure"):
        save_to_json("structure_ia.json", st.session_state["structure"])
        st.sidebar.success("✅ Structure exportée.")
    else:
        st.sidebar.warning("❌ Aucune structure à exporter.")

if st.sidebar.button("Exporter Tableau enrichi"):
    enriched = st.session_state.get("enriched")
    if enriched:
        save_to_json("enriched_table.json", enriched)
        export_enriched_to_csv(enriched)
        st.sidebar.success("✅ Tableau enrichi exporté.")
    else:
        st.sidebar.warning("❌ Aucun tableau enrichi à exporter.")

st.sidebar.markdown("---")
st.sidebar.subheader("📤 Export depuis la base SQLite")

if st.sidebar.button("Exporter SERP (DB)"):
    export_serp_from_db()
    st.sidebar.success("✅ SERP depuis DB exporté.")

if st.sidebar.button("Exporter Sitemaps (DB)"):
    export_sitemap_from_db()
    st.sidebar.success("✅ Sitemaps depuis DB exportés.")

st.sidebar.subheader("📥 Charger depuis la base SQLite")

if st.sidebar.button("Charger SERP (DB)"):
    serp = load_serp_from_db()
    if serp:
        st.session_state["serp_urls"] = serp
        st.success("✅ SERP chargé depuis DB.")
    else:
        st.warning("❌ Aucun résultat SERP en base.")

if st.sidebar.button("Charger Sitemaps (DB)"):
    sitemaps = load_sitemap_from_db()
    if sitemaps:
        st.session_state["sitemap_urls"] = sitemaps
        st.success("✅ Sitemaps chargés depuis DB.")
    else:
        st.warning("❌ Aucune URL sitemap en base.")

if st.sidebar.button("Charger Structure (DB)"):
    struct = load_structure_from_db()
    if struct:
        st.session_state["structure"] = struct
        st.success("✅ Structure IA chargée depuis DB.")
    else:
        st.warning("❌ Aucune structure en base.")

if st.sidebar.button("Charger Tableau enrichi (DB)"):
    enriched = load_enriched_from_db()
    if enriched:
        st.session_state["enriched"] = enriched
        st.success("✅ Tableau enrichi chargé depuis DB.")
    else:
        st.warning("❌ Aucun tableau enrichi en base.")

# --- Interface principale ---
mode = st.radio("Mode d'entrée", ["SerpAPI", "Manuel (liste d'URLs)", "Liste de titres"])
context = st.text_area("Contexte du site", "Bienvenue à Annecy est un site communautaire choc pour touristes et locaux...")
site_name = st.text_input("Nom du site", "Bienvenue à Annecy")

if mode == "SerpAPI":
    keyword = st.text_input("Mot-clé principal", "sortir à Annecy")
    if st.button("Chercher SERP"):
        urls = get_serpapi_results(keyword)
        if urls:
            st.session_state["serp_urls"] = urls
            st.session_state["serp_keyword"] = keyword
            store_serp_results(keyword, urls)
            st.success(f"✅ {len(urls)} URLs récupérées.")
        else:
            st.warning("❌ Aucune URL récupérée.")

    if "serp_urls" in st.session_state:
        selected_urls = []
        st.subheader("Sélection des résultats SERP")
        for i, url in enumerate(st.session_state["serp_urls"]):
            if st.checkbox(f"{url}", value=True, key=f"url_{i}"):
                selected_urls.append(url)
        if selected_urls and st.button("Explorer les sitemaps"):
            all_urls_flat = []
            for url in selected_urls:
                sitemaps = get_sitemap_from_robots(url)
                for sitemap_url in sitemaps:
                    page_urls = get_all_sitemaps(sitemap_url)
                    all_urls_flat.extend(page_urls)
            if all_urls_flat:
                st.session_state["sitemap_urls"] = all_urls_flat
                save_to_csv("urls_sitemap.csv", all_urls_flat)
                store_sitemap_urls(all_urls_flat)
                st.success(f"✅ {len(all_urls_flat)} URLs collectées.")
            else:
                st.warning("❌ Aucune URL sitemap extraite.")

elif mode == "Manuel (liste d'URLs)":
    raw_urls = st.text_area("Liste d'URLs (une par ligne)", "https://www.annecy-ville.fr\nhttps://www.annecy.fr\nhttps://www.lac-annecy.com")
    if st.button("Explorer les sitemaps"):
        custom_urls = [url.strip() for url in raw_urls.splitlines() if url.strip()]
        all_urls_flat = []
        for url in custom_urls:
            sitemaps = get_sitemap_from_robots(url)
            for sitemap_url in sitemaps:
                page_urls = get_all_sitemaps(sitemap_url)
                all_urls_flat.extend(page_urls)
        if all_urls_flat:
            st.session_state["sitemap_urls"] = all_urls_flat
            st.session_state["serp_urls"] = custom_urls
            save_to_csv("urls_sitemap.csv", all_urls_flat)
            store_sitemap_urls(all_urls_flat)
            st.success(f"✅ {len(all_urls_flat)} URLs extraites.")
        else:
            st.warning("❌ Aucune URL sitemap extraite.")

if mode in ["SerpAPI", "Manuel (liste d'URLs)"] and "sitemap_urls" in st.session_state:
    st.subheader("Modifier la liste d'URLs extraites")
    urls_text = st.text_area("URLs à structurer", "\n".join(st.session_state["sitemap_urls"]))
    final_urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if st.button("Générer structure avec l'IA"):
        structure = generate_structure_with_ai(context, site_name, st.session_state.get("serp_urls", []), final_urls, selected_api)
        if "error" not in structure:
            st.session_state["structure"] = structure
            save_to_json("structure_ia.json", structure)
            store_structure_in_sqlite(structure)
            st.subheader("Structure JSON")
            structure_json = st.text_area("Modifier structure JSON", json.dumps(structure, indent=2))
            if st.button("Valider la structure"):
                try:
                    validated_structure = json.loads(structure_json)
                    with st.spinner("Enrichissement en cours..."):
                        enriched_data = enrich_structure_to_table(validated_structure, context, site_name, selected_api)
                        st.session_state["enriched"] = enriched_data
                        save_to_json("enriched_table.json", enriched_data)
                        export_enriched_to_csv(enriched_data)
                        store_enriched_pages_in_sqlite(enriched_data)
                        st.subheader("Tableau JSON")
                        st.json(enriched_data)
                        st.subheader("Markdown")
                        st.code(generate_markdown_table(enriched_data), language="markdown")
                        st.dataframe(enriched_data["pages"])
                        st.download_button("Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
                        st.success("✅ Enrichissement terminé.")
                except json.JSONDecodeError as e:
                    st.error(f"Erreur JSON dans la structure : {e}")

elif mode == "Liste de titres":
    titles = st.text_area("Titres H1 (séparés par virgule)", "Soin visage microdermabrasion Annecy, Massage Kobido Annecy").split(",")
    if st.button("Générer"):
        cleaned_titles = [t.strip() for t in titles if t.strip()]
        if cleaned_titles and context and site_name:
            with st.spinner(f"Génération avec {selected_api}..."):
                enriched_data = generate_enriched_table_from_titles(cleaned_titles, context, site_name, selected_api)
                if "error" not in enriched_data:
                    st.session_state["enriched"] = enriched_data
                    save_to_json("enriched_table.json", enriched_data)
                    export_enriched_to_csv(enriched_data)
                    store_enriched_pages_in_sqlite(enriched_data)
                    st.subheader("Tableau JSON")
                    st.json(enriched_data)
                    st.subheader("Markdown")
                    st.code(generate_markdown_table(enriched_data), language="markdown")
                    st.dataframe(enriched_data["pages"])
                    st.download_button("Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
                    st.success("✅ Tableau généré.")
        else:
            st.error("Veuillez remplir les titres, le contexte et le nom du site.")
