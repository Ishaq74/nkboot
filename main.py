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

# --- Rechargement depuis fichier ---
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Recharger depuis fichier")

if st.sidebar.button("Charger SERP JSON"):
    serp = load_from_json("serpapi_results.json")
    if serp:
        st.session_state["serp_urls"] = serp
        st.success("✅ SERP rechargé.")
        st.write(serp)
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger URLs Sitemap"):
    sitemap_urls = load_from_csv("urls_sitemap.csv")
    if sitemap_urls:
        st.session_state["sitemap_urls"] = sitemap_urls
        st.success("✅ Sitemaps rechargés.")
        st.write(sitemap_urls)
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger Structure IA"):
    struct = load_from_json("structure_ia.json")
    if struct:
        st.session_state["structure"] = struct
        st.success("✅ Structure IA rechargée.")
        st.json(struct)
    else:
        st.warning("❌ Fichier introuvable ou vide.")

if st.sidebar.button("Charger Tableau enrichi"):
    enriched = load_from_json("enriched_table.json")
    if enriched:
        st.session_state["enriched"] = enriched
        st.success("✅ Tableau enrichi rechargé.")
        st.json(enriched)
    else:
        st.warning("❌ Fichier introuvable ou vide.")

# --- Export depuis session ---
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

# --- Export depuis la base ---
st.sidebar.markdown("---")
st.sidebar.subheader("📤 Export depuis la base SQLite")

if st.sidebar.button("Exporter SERP (DB)"):
    export_serp_from_db()
    st.sidebar.success("✅ SERP depuis DB exporté.")

if st.sidebar.button("Exporter Sitemaps (DB)"):
    export_sitemap_from_db()

if st.sidebar.button("Exporter Structure (DB)"):
    from database import export_structure_from_db
    export_structure_from_db()
    st.sidebar.success("✅ Structure exportée localement.")

if st.sidebar.button("Exporter Tableau enrichi (DB)"):
    from database import export_enriched_from_db
    export_enriched_from_db()
    st.sidebar.success("✅ Tableau enrichi exporté (JSON + CSV).")
    st.sidebar.success("✅ Sitemaps depuis DB exportés.")

# --- Chargement depuis base ---
st.sidebar.subheader("📥 Charger depuis la base SQLite")

if st.sidebar.button("Charger SERP (DB)"):
    serp = load_serp_from_db()
    if serp:
        st.session_state["serp_urls"] = serp
        st.success("✅ SERP chargé depuis DB.")
        st.write(serp)
    else:
        st.warning("❌ Aucun résultat SERP en base.")

if st.sidebar.button("Charger Sitemaps (DB)"):
    sitemaps = load_sitemap_from_db()
    if sitemaps:
        st.session_state["sitemap_urls"] = sitemaps
        st.success("✅ Sitemaps chargés depuis DB.")
        st.write(sitemaps)
    else:
        st.warning("❌ Aucune URL sitemap en base.")

if st.sidebar.button("Charger Structure (DB)"):
    struct = load_structure_from_db()
    if struct:
        st.session_state["structure"] = struct
        st.success("✅ Structure IA chargée depuis DB.")
        st.json(struct)
    else:
        st.warning("❌ Aucune structure en base.")

if st.sidebar.button("Charger Tableau enrichi (DB)"):
    enriched = load_enriched_from_db()
    if enriched:
        st.session_state["enriched"] = enriched
        st.success("✅ Tableau enrichi chargé depuis DB.")
        st.json(enriched)
    else:
        st.warning("❌ Aucun tableau enrichi en base.")

# =============================
# === INTERFACE PRINCIPALE ===
# =============================

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
            st.download_button("📥 Télécharger SERP JSON", json.dumps(urls), "serpapi_results.json")
        else:
            st.warning("❌ Aucune URL récupérée.")

if "serp_urls" in st.session_state:
    st.subheader("Sélection des résultats SERP")
    selected_urls = [url for i, url in enumerate(st.session_state["serp_urls"]) if st.checkbox(url, value=True, key=f"url_{i}")]
    if selected_urls and st.button("Explorer les sitemaps"):
        all_urls_flat = []
        for url in selected_urls:
            sitemaps = get_sitemap_from_robots(url)
            for sitemap_url in sitemaps:
                all_urls_flat.extend(get_all_sitemaps(sitemap_url))
        if all_urls_flat:
            st.session_state["sitemap_urls"] = all_urls_flat
            save_to_csv("urls_sitemap.csv", all_urls_flat)
            store_sitemap_urls(all_urls_flat)
            st.success(f"✅ {len(all_urls_flat)} URLs collectées.")
            st.download_button("📥 Télécharger URLs Sitemap", "\n".join(all_urls_flat), "urls_sitemap.csv")
        else:
            st.warning("❌ Aucune URL sitemap trouvée.")

elif mode == "Manuel (liste d'URLs)":
    raw_urls = st.text_area("Liste d'URLs (une par ligne)", "https://www.annecy-ville.fr\nhttps://www.annecy.fr")
    if st.button("Explorer les sitemaps"):
        custom_urls = [url.strip() for url in raw_urls.splitlines() if url.strip()]
        all_urls_flat = []
        for url in custom_urls:
            sitemaps = get_sitemap_from_robots(url)
            for sitemap_url in sitemaps:
                all_urls_flat.extend(get_all_sitemaps(sitemap_url))
        if all_urls_flat:
            st.session_state["sitemap_urls"] = all_urls_flat
            st.session_state["serp_urls"] = custom_urls
            save_to_csv("urls_sitemap.csv", all_urls_flat)
            store_sitemap_urls(all_urls_flat)
            st.success(f"✅ {len(all_urls_flat)} URLs extraites.")
            st.download_button("📥 Télécharger Sitemap", "\n".join(all_urls_flat), "urls_sitemap.csv")
        else:
            st.warning("❌ Aucune URL sitemap trouvée.")

if mode in ["SerpAPI", "Manuel (liste d'URLs)"] and "sitemap_urls" in st.session_state:
    st.subheader("Générer structure IA")
    urls_text = st.text_area("URLs à structurer", "\n".join(st.session_state["sitemap_urls"]))
    final_urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if st.button("Générer structure avec l'IA"):
        structure = generate_structure_with_ai(context, site_name, st.session_state.get("serp_urls", []), final_urls, selected_api)
        if "error" not in structure:
            st.session_state["structure"] = structure
            save_to_json("structure_ia.json", structure)
            store_structure_in_sqlite(structure)
            st.success("✅ Structure générée.")
            st.json(structure)
            st.download_button("📥 Télécharger Structure JSON", json.dumps(structure, indent=2), "structure_ia.json")

if "structure" in st.session_state:
    st.subheader("Valider & enrichir la structure")
    structure_json = st.text_area("Structure JSON", json.dumps(st.session_state["structure"], indent=2))
    if st.button("Valider la structure"):
        try:
            validated_structure = json.loads(structure_json)
            with st.spinner("Enrichissement en cours..."):
                enriched_data = enrich_structure_to_table(validated_structure, context, site_name, selected_api)
                st.session_state["enriched"] = enriched_data
                save_to_json("enriched_table.json", enriched_data)
                export_enriched_to_csv(enriched_data)
                store_enriched_pages_in_sqlite(enriched_data)
                st.success("✅ Enrichissement terminé.")
                st.json(enriched_data)
                st.download_button("📥 Télécharger JSON enrichi", json.dumps(enriched_data, indent=2), "enriched_table.json")
                st.download_button("📥 Télécharger CSV enrichi", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
        except json.JSONDecodeError as e:
            st.error(f"Erreur JSON : {e}")

elif mode == "Liste de titres":
    titles = st.text_area("Titres H1 (séparés par virgule)", "Massage Kobido Annecy, Soin visage LED Annecy").split(",")
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
                    st.success("✅ Enrichissement terminé.")
                    st.json(enriched_data)
                    st.download_button("📥 Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
        else:
            st.error("Veuillez remplir tous les champs requis.")
