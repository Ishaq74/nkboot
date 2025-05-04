import streamlit as st
import json
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from utils import get_serpapi_results, fetch_page_content
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROK_API_KEY     = os.getenv("GROK_API_KEY")

###############################################################################
# TEST API (inchangé)
###############################################################################
def test_api(selected_api):
    st.info(f"Tentative de test de l'API : {selected_api}")
    if selected_api == "Gemini":
        if not GEMINI_API_KEY:
            st.error("Clé Gemini manquante.")
            return False
        try:
            model = ChatGoogleGenerativeAI(model="gemini-2.0-flash",
                                           google_api_key=GEMINI_API_KEY)
            response = model.invoke("Test.")
            if response:
                st.success("Gemini OK.")
                return True
        except Exception as e:
            st.error(f"Erreur Gemini : {e}")
            return False
    elif selected_api == "Anthropic":
        if not ANTHROPIC_API_KEY:
            st.error("Clé Anthropic manquante.")
            return False
        try:
            model = ChatAnthropic(model="claude-3-opus-20240229",
                                  api_key=ANTHROPIC_API_KEY)
            response = model.invoke("Test.")
            if response:
                st.success("Anthropic OK.")
                return True
        except Exception as e:
            st.error(f"Erreur Anthropic : {e}")
            return False
    elif selected_api == "Grok":
        if not GROK_API_KEY:
            st.error("Clé Grok manquante.")
            return False
        try:
            headers = {"Content-Type": "application/json",
                       "Authorization": f"Bearer {GROK_API_KEY}"}
            data = {
                "messages": [{"role": "user", "content": "Test."}],
                "model": "grok-2-latest",
                "stream": False,
                "temperature": 0
            }
            response = requests.post("https://api.x.ai/v1/chat/completions",
                                     headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            st.success(f"Grok OK. Réponse : {content}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                st.error("Erreur Grok : 403 Forbidden.")
            else:
                st.error(f"Erreur Grok : {e}")
            return False

###############################################################################
# GET MODEL (inchangé)
###############################################################################
def get_model(selected_api):
    if selected_api == "Gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash",
                                      google_api_key=GEMINI_API_KEY)
    elif selected_api == "Anthropic":
        return ChatAnthropic(model="claude-3-opus-20240229",
                             api_key=ANTHROPIC_API_KEY)
    elif selected_api == "Grok":
        return "grok"

###############################################################################
# MERGE (inchangé)
###############################################################################
def merge_structures(structure1, structure2):
    merged = structure1.copy()
    if not isinstance(structure2, dict):
        st.warning("Structure2 n'est pas un dictionnaire, tentative de conversion...")
        if isinstance(structure2, list):
            structure2 = {"Unknown_Category": {"pages": structure2}}
        else:
            return merged
    for category, data in structure2.items():
        if category in merged:
            merged[category]["pages"].extend(data.get("pages", []))
        else:
            merged[category] = data
    return merged

###############################################################################
# NOUVEAU : normalisation si le LLM renvoie un nœud unique
###############################################################################
def normalize_node_dict(s):
    """
    Si le LLM renvoie un seul nœud sous forme {'title': ..., 'slug': ...},
    le convertir en {'<slug>': s} pour rester compatible avec merge_structures().
    """
    if isinstance(s, dict) and 'title' in s and 'slug' in s:
        return {s['slug']: s}
    return s

###############################################################################
# GENERATE STRUCTURE (prompt mis à jour + nettoyage json + normalisation)
###############################################################################
def generate_structure_with_ai(context, site_name, serp_data, all_urls,
                               selected_api, batch_size=50):
    st.info(f"Préparation de la génération de structure pour '{site_name}'")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}

    total_urls   = len(all_urls)
    total_batches = (total_urls + batch_size - 1) // batch_size
    st.info(f"Total URLs à traiter : {total_urls} | Lots à générer : {total_batches}")

    full_structure = {}
    progress_bar   = st.progress(0)

    for i in range(0, total_urls, batch_size):
        batch_urls = all_urls[i:i + batch_size]
        batch_num  = i // batch_size + 1
        st.info(f"Traitement du lot {batch_num}/{total_batches} ({len(batch_urls)} URLs)")

        # --- PROMPT mis à jour ---
        prompt = (
            f"Tu es un expert en architecture SEO.\n"
            f"Contexte : \"{context}\"\n"
            f"Nom du site : \"{site_name}\"\n\n"
            "Génère une structure hiérarchique optimale à partir des URLs ci‑dessous.\n"
            "### Contraintes\n"
            "• Chaque nœud : title, slug (kebab-case, sans accent, ≤100 car, unique), "
            "type_page ('category' | 'subcategory' | 'page'), mot_cle_principal_unique, "
            "et éventuellement pages (liste).\n"
            "• Convertis title→slug. Si deux titres donnent le même slug, fusionne leurs contenus.\n"
            "• Maximum 4 niveaux, regroupe les quasi‑doublons (ex. pages week‑end).\n"
            "• Réponds UNIQUEMENT par un JSON strict : {{'structure': {{...}}, 'debug_notes': []}}\n\n"
            f"URLs SERP : {json.dumps(serp_data, ensure_ascii=False)}\n"
            f"URLs du lot : {json.dumps(batch_urls, ensure_ascii=False)}"
        )
        # -------------------------

        st.info(f"Envoi du prompt pour le lot {batch_num} (taille : {len(prompt)} caractères)")
        try:
            if selected_api == "Grok":
                headers = {"Content-Type": "application/json",
                           "Authorization": f"Bearer {GROK_API_KEY}"}
                data = {"messages": [{"role": "user", "content": prompt}],
                        "model": "grok-2-latest", "stream": False, "temperature": 0}
                response = requests.post("https://api.x.ai/v1/chat/completions",
                                         headers=headers, json=data)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip()
            else:
                response = model.invoke(prompt)
                content = response.content.strip()

            if not content:
                st.warning(f"Réponse vide de {selected_api} pour le lot {batch_num}. Passage au suivant.")
                continue

            # Nettoyage balises ```
            if content.startswith("```"):
                content = content.split("```")[1].strip()
            # Nettoyage préfixe "json"
            if content.lower().startswith("json"):
                content = content[4:].lstrip(" :").lstrip()

            st.write(f"Réponse brute de {selected_api} pour le lot {batch_num} : {content[:400]}...")

            try:
                parsed_response = json.loads(content)
                structure = parsed_response.get("structure", {})
                structure = normalize_node_dict(structure)   # <- ajout
                if not isinstance(structure, dict):
                    st.warning(f"Structure inattendue pour le lot {batch_num} : {structure}. Passage au suivant.")
                    continue
                full_structure = merge_structures(full_structure, structure)
                st.success(f"Structure du lot {batch_num} intégrée avec succès.")
                num_pages = sum(len(d.get("pages", [])) for d in full_structure.values())
                st.info(f"Nombre total de pages dans la structure actuelle : {num_pages}")
            except json.JSONDecodeError as e:
                st.warning(f"JSON invalide pour le lot {batch_num} : {e}. Passage au suivant.")
                st.write(f"Extrait autour de l'erreur : {content[max(0, e.pos-20):e.pos+20]}")
                continue
        except Exception as e:
            st.warning(f"Erreur inattendue lors du lot {batch_num} : {e}. Passage au suivant.")
            continue

        progress = min((i + batch_size) / total_urls, 1.0)
        progress_bar.progress(progress)

    st.success(f"Structure finale générée avec succès ! Total URLs traitées : {total_urls}")
    st.info(f"Structure finale (extrait) : {json.dumps(full_structure)[:200]}...")
    return {"structure": full_structure}

###############################################################################
# ENRICHISSEMENT DE LA STRUCTURE EN TABLEAU
###############################################################################
def enrich_structure_to_table(structure, context, site_name, selected_api):
    st.info(f"Enrichissement de la structure en tableau détaillé pour « {site_name} »")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}

    enriched_pages = []
    all_keywords, all_slugs = set(), set()
    total_pages = sum(len(data["pages"]) for data in structure["structure"].values())
    st.info(f"Nombre total de pages : {total_pages}")
    progress_bar = st.progress(0)

    page_count = 0
    for category, data in structure["structure"].items():
        cat_keyword = data["mot_cle_principal_unique"]
        for page in data["pages"]:
            page_count += 1
            page_keyword = page["mot_cle_principal_unique"]
            st.info(f"Page {page_count}/{total_pages} : « {page_keyword} »")

            serp_urls = get_serpapi_results(page_keyword)
            serp_content = "".join(
                f"Contenu {url}:\n{fetch_page_content(url)[:1000]}\n\n"
                for url in serp_urls
                if "Erreur" not in fetch_page_content(url)
            )

            prompt = (
                f"Contexte « {site_name} » : {context}. "
                f"Catégorie : {category} (mot‑clé : {cat_keyword}). "
                f"Page : {page['type_page']} « {page_keyword} ». "
                f"Contenu SERP : {serp_content}. "
                "Génère un tableau SEO 18 colonnes : Type de contenu, Titre H1, Lien de parenté, "
                "Objectif, Mot‑clé principal unique, Trafic estimé, Top 5 SERP, "
                "Mots‑clés secondaires, Intention, Title, Meta Description, Alt images, "
                "EEAT, Liens intro, Liens pages filles, Liens pages sœurs, CTA, Permalink, "
                "Statut de production. "
                "Retourne uniquement : {'page': {colonne: valeur}}."
            )

            try:
                if selected_api == "Grok":
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {GROK_API_KEY}"
                    }
                    data = {
                        "messages": [{"role": "user", "content": prompt}],
                        "model": "grok-2-latest",
                        "stream": False,
                        "temperature": 0
                    }
                    response = requests.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers=headers,
                        json=data
                    )
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"].strip()
                else:
                    content = model.invoke(prompt).content.strip()

                if content.startswith("```json"):
                    content = content[7:].rstrip("```").strip()

                page_data = json.loads(content)["page"]

                # Unicité mots‑clés & slugs
                if page_data["Mot-clé principal unique"] in all_keywords:
                    page_data["Mot-clé principal unique"] += f" {len(all_keywords)+1}"
                all_keywords.add(page_data["Mot-clé principal unique"])

                if page_data["Permalink"] in all_slugs:
                    page_data["Permalink"] += f"-{len(all_slugs)+1}"
                all_slugs.add(page_data["Permalink"])

                enriched_pages.append(page_data)
                progress_bar.progress(page_count / total_pages)
            except Exception as e:
                st.error(f"Erreur enrichissement « {page_keyword} » : {e}")

    st.success(f"Tableau enrichi généré. Total pages : {len(enriched_pages)}")
    return {"pages": enriched_pages}

###############################################################################
# ENRICHISSEMENT À PARTIR DES TITRES
###############################################################################
def generate_enriched_table_from_titles(titles, context, site_name, selected_api):
    st.info(f"Génération du tableau enrichi depuis titres pour « {site_name} »")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}

    enriched_pages = []
    all_keywords, all_slugs = set(), set()
    total_titles = len(titles)
    progress_bar = st.progress(0)

    for idx, title in enumerate(titles, 1):
        st.info(f"Titre {idx}/{total_titles} : « {title.strip()} »")

        serp_urls = get_serpapi_results(title)
        serp_content = "".join(
            f"Contenu {url}:\n{fetch_page_content(url)[:1000]}\n\n"
            for url in serp_urls
            if "Erreur" not in fetch_page_content(url)
        )

        prompt = (
            f"Contexte « {site_name} » : {context}. "
            f"Titre H1 : {title}. "
            f"Contenu SERP : {serp_content}. "
            "Génère un tableau SEO 18 colonnes (mêmes colonnes que précédemment). "
            "Retourne uniquement JSON : {'page': {...}}."
        )

        try:
            if selected_api == "Grok":
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROK_API_KEY}"
                }
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "grok-2-latest",
                    "stream": False,
                    "temperature": 0
                }
                response = requests.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip()
            else:
                content = model.invoke(prompt).content.strip()

            if content.startswith("```json"):
                content = content[7:].rstrip("```").strip()

            page_data = json.loads(content)["page"]

            if page_data["Mot-clé principal unique"] in all_keywords:
                page_data["Mot-clé principal unique"] += f" {len(all_keywords)+1}"
            all_keywords.add(page_data["Mot-clé principal unique"])

            if page_data["Permalink"] in all_slugs:
                page_data["Permalink"] += f"-{len(all_slugs)+1}"
            all_slugs.add(page_data["Permalink"])

            enriched_pages.append(page_data)
            progress_bar.progress(idx / total_titles)
        except Exception as e:
            st.error(f"Erreur enrichissement « {title} » : {e}")

    st.success(f"Tableau enrichi généré. Total : {len(enriched_pages)}")
    return {"pages": enriched_pages}
