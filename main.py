import streamlit as st
import json
from utils import get_serpapi_results, get_sitemap_from_robots, get_all_sitemaps, load_from_json, load_from_csv, save_to_json, save_to_csv
from database import store_structure_in_sqlite, store_enriched_pages_in_sqlite
from ai_processing import generate_structure_with_ai, enrich_structure_to_table, generate_enriched_table_from_titles, test_api
from output import generate_markdown, generate_markdown_table, generate_csv

st.title("Générateur de structure de site SEO")

selected_api = st.sidebar.selectbox("Choisir API", ["Gemini", "Anthropic", "Grok"])
if st.sidebar.button("Tester API"):
    test_api(selected_api)

st.sidebar.markdown("---")

st.sidebar.subheader("Recharger depuis fichier")
if st.sidebar.button("Charger SERP JSON"):
    st.session_state["serp_urls"] = load_from_json("serpapi_results.json")
    st.success("SERP rechargé depuis fichier.")
if st.sidebar.button("Charger URLs Sitemap"):
    st.session_state["sitemap_urls"] = load_from_csv("urls_sitemap.csv")
    st.success("Sitemaps rechargés depuis fichier.")
if st.sidebar.button("Charger Structure IA"):
    st.session_state["structure"] = load_from_json("structure_ia.json")
    st.success("Structure IA rechargée.")
if st.sidebar.button("Charger Tableau enrichi"):
    st.session_state["enriched"] = load_from_json("enriched_table.json")
    st.success("Tableau enrichi rechargé.")

mode = st.radio("Mode d'entrée", ["SerpAPI", "Manuel (liste d'URLs)", "Liste de titres"])
context = st.text_area("Contexte du site", "Bienvenue à Annecy est un site communautaire choc pour touristes et locaux...")
site_name = st.text_input("Nom du site", "Bienvenue à Annecy")

if mode == "SerpAPI":
    keyword = st.text_input("Mot-clé principal", "sortir à Annecy")
    if st.button("Chercher SERP"):
        urls = get_serpapi_results(keyword)
        st.session_state["serp_urls"] = urls

    if "serp_urls" in st.session_state:
        selected_urls = []
        st.subheader("Sélection des résultats SERP")
        for i, url in enumerate(st.session_state["serp_urls"]):
            if st.checkbox(f"{url}", value=True, key=f"url_{i}"):
                selected_urls.append(url)
        if selected_urls and st.button("Explorer les sitemaps"):
            all_sitemaps = {}
            all_urls_flat = []
            for url in selected_urls:
                st.write(f"Sitemaps pour : {url}")
                sitemaps = get_sitemap_from_robots(url)
                for sitemap_url in sitemaps:
                    page_urls = get_all_sitemaps(sitemap_url)
                    all_sitemaps[sitemap_url] = page_urls
                    all_urls_flat.extend(page_urls)
            st.session_state["sitemap_urls"] = all_urls_flat
            save_to_csv("urls_sitemap.csv", all_urls_flat)
            st.write(f"Total URLs : {len(all_urls_flat)}")

    if "sitemap_urls" in st.session_state:
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
                            store_enriched_pages_in_sqlite(enriched_data)
                            st.subheader("Tableau JSON")
                            st.json(enriched_data)
                            st.subheader("Markdown")
                            st.code(generate_markdown_table(enriched_data), language="markdown")
                            st.dataframe(enriched_data["pages"])
                            st.download_button("Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
                            st.success("Fini !")
                    except json.JSONDecodeError as e:
                        st.error(f"Erreur JSON dans la structure : {e}")

elif mode == "Manuel (liste d'URLs)":
    raw_urls = st.text_area("Liste d'URLs (une par ligne)", "https://www.annecy-ville.fr\nhttps://www.annecy.fr\nhttps://www.lac-annecy.com")
    if st.button("Explorer les sitemaps"):
        custom_urls = [url.strip() for url in raw_urls.splitlines() if url.strip()]
        all_sitemaps = {}
        all_urls_flat = []
        for url in custom_urls:
            sitemaps = get_sitemap_from_robots(url)
            for sitemap_url in sitemaps:
                page_urls = get_all_sitemaps(sitemap_url)
                all_sitemaps[sitemap_url] = page_urls
                all_urls_flat.extend(page_urls)
        st.session_state["sitemap_urls"] = all_urls_flat
        st.session_state["serp_urls"] = custom_urls
        save_to_csv("urls_sitemap.csv", all_urls_flat)
        st.write(f"Total URLs extraites : {len(all_urls_flat)}")

    if "sitemap_urls" in st.session_state:
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
                            store_enriched_pages_in_sqlite(enriched_data)
                            st.subheader("Tableau JSON")
                            st.json(enriched_data)
                            st.subheader("Markdown")
                            st.code(generate_markdown_table(enriched_data), language="markdown")
                            st.dataframe(enriched_data["pages"])
                            st.download_button("Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
                            st.success("Fini !")
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
                    store_enriched_pages_in_sqlite(enriched_data)
                    st.subheader("Tableau JSON")
                    st.json(enriched_data)
                    st.subheader("Markdown")
                    st.code(generate_markdown_table(enriched_data), language="markdown")
                    st.dataframe(enriched_data["pages"])
                    st.download_button("Télécharger CSV", generate_csv(enriched_data), "enriched_pages.csv", "text/csv")
                    st.success("Tableau généré !")
        else:
            st.error("Veuillez remplir les titres, le contexte et le nom du site.")
