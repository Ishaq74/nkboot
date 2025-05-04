import streamlit as st
import json
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from utils import get_serpapi_results, fetch_page_content
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

def test_api(selected_api):
    st.info(f"Tentative de test de l'API : {selected_api}")
    if selected_api == "Gemini":
        if not GEMINI_API_KEY:
            st.error("Clé Gemini manquante.")
            return False
        try:
            model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)
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
            model = ChatAnthropic(model="claude-3-opus-20240229", api_key=ANTHROPIC_API_KEY)
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
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"}
            data = {
                "messages": [{"role": "user", "content": "Test."}],
                "model": "grok-2-latest",
                "stream": False,
                "temperature": 0
            }
            response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            st.success(f"Grok OK. Réponse : {content}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                st.error(f"Erreur Grok : 403 Forbidden. Vérifiez la clé API ou les permissions sur https://api.x.ai. Réponse brute : {e.response.text}")
            else:
                st.error(f"Erreur Grok : {e}")
            return False

def get_model(selected_api):
    if selected_api == "Gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)
    elif selected_api == "Anthropic":
        return ChatAnthropic(model="claude-3-opus-20240229", api_key=ANTHROPIC_API_KEY)
    elif selected_api == "Grok":
        return "grok"

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

def generate_structure_with_ai(context, site_name, serp_data, all_urls, selected_api, batch_size=50):
    st.info(f"Préparation de la génération de structure pour '{site_name}'")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}

    total_urls = len(all_urls)
    total_batches = (total_urls + batch_size - 1) // batch_size
    st.info(f"Total URLs à traiter : {total_urls} | Lots à générer : {total_batches}")

    full_structure = {}
    progress_bar = st.progress(0)

    for i in range(0, total_urls, batch_size):
        batch_urls = all_urls[i:i + batch_size]
        batch_num = i // batch_size + 1
        st.info(f"Traitement du lot {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
        prompt = (
            f"Contexte du site '{site_name}': {context}. "
            "Objectif : Créer une structure SEO PARFAITE en s'inspirant de ce lot d’URLs. "
            f"URLs SERP : {serp_data}. "
            f"URLs du lot : {json.dumps(batch_urls)}. "
            "Étapes : "
            "1) Analyse : Identifie types ('Page d’accueil', 'Page produit', 'Article de blog', 'Page de service', 'Page de catégorie de produit', 'Page de catégorie de blog'). "
            "2) Génère un mot-clé principal UNIQUE basé sur le dernier slug + contexte (ex. '/produit/shampoing-bio' -> 'Acheter shampoing bio Annecy'). "
            "3) Contrôle : Vérifie unicité et absence de cannibalisation. "
            "Structure : "
            "- Catégories réelles (ex. 'Produits') avec 'mot_cle_principal_unique'. "
            "- Sous-pages avec 'type_page', 'mot_cle_principal_unique'. "
            "Retourne un JSON valide avec une clé 'structure' : "
            "{'structure': {catégories -> {'mot_cle_principal_unique', 'pages': [{'type_page', 'mot_cle_principal_unique'}]}}}. "
            "PAS de champs 'url_sitemap' ou 'nouvelle_page', PAS de troncature, syntaxe JSON stricte."
        )
        st.info(f"Envoi du prompt pour le lot {batch_num} (taille : {len(prompt)} caractères)")
        try:
            if selected_api == "Grok":
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"}
                data = {"messages": [{"role": "user", "content": prompt}], "model": "grok-2-latest", "stream": False, "temperature": 0}
                response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip()
            else:
                response = model.invoke(prompt)
                content = response.content.strip()

            if not content:
                st.warning(f"Réponse vide de {selected_api} pour le lot {batch_num}. Passage au suivant.")
                continue

            if content.startswith("```json"):
                content = content[7:].rstrip("```").strip()
            elif content.startswith("```"):
                content = content[3:].rstrip("```").strip()

            st.write(f"Réponse brute de {selected_api} pour le lot {batch_num} : {content}")

            try:
                parsed_response = json.loads(content)
                structure = parsed_response.get("structure", {})
                if not isinstance(structure, dict):
                    st.warning(f"Structure inattendue pour le lot {batch_num} : {structure}. Passage au suivant.")
                    continue
                full_structure = merge_structures(full_structure, structure)
                st.success(f"Structure du lot {batch_num} intégrée avec succès.")
                num_pages = sum(len(data.get("pages", [])) for data in full_structure.values())
                st.info(f"Nombre total de pages dans la structure actuelle : {num_pages}")
            except json.JSONDecodeError as e:
                st.warning(f"JSON invalide pour le lot {batch_num} : {e}. Passage au suivant.")
                st.write(f"Position de l'erreur : {e.pos}, ligne {e.lineno}, colonne {e.colno}")
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


def enrich_structure_to_table(structure, context, site_name, selected_api):
    st.info(f"Enrichissement de la structure en tableau détaillé pour '{site_name}'")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}
    
    enriched_pages = []
    all_keywords = set()
    all_slugs = set()
    total_pages = sum(len(data["pages"]) for data in structure["structure"].values())
    st.info(f"Nombre total de pages à enrichir : {total_pages}")
    progress_bar = st.progress(0)
    
    page_count = 0
    for category, data in structure["structure"].items():
        cat_keyword = data["mot_cle_principal_unique"]
        for page in data["pages"]:
            page_count += 1
            page_keyword = page["mot_cle_principal_unique"]
            st.info(f"Enrichissement de la page {page_count}/{total_pages} : '{page_keyword}'")
            serp_urls = get_serpapi_results(page_keyword)
            serp_content = "".join([f"Contenu {url}:\n{fetch_page_content(url)[:1000]}\n\n" for url in serp_urls if "Erreur" not in fetch_page_content(url)])
            prompt = (
                f"Contexte '{site_name}': {context}. "
                f"Catégorie : {category} (mot-clé : {cat_keyword}). "
                f"Page : {page['type_page']} avec '{page_keyword}'. "
                f"Contenu SERP : {serp_content}. "
                "Générer tableau SEO 18 colonnes : Type de contenu, Titre H1 Page, Lien de parenté, Objectif, Mot-clé principal unique, "
                "Trafic estimé, Top 5 des SERP, Mots-clés secondaires, Intention utilisateur, Balise Title, Meta Description, Alt des images, "
                "EAAT, Liens principaux pour l’intro, Liens pages filles, Liens pages sœurs, Appels à l’action, Permalink, Statut de production. "
                "Retourne JSON : {'page': {colonne: valeur}}."
            )
            st.info(f"Envoi du prompt pour enrichir '{page_keyword}' (taille : {len(prompt)} caractères)")
            try:
                if selected_api == "Grok":
                    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"}
                    data = {"messages": [{"role": "user", "content": prompt}], "model": "grok-2-latest", "stream": False, "temperature": 0}
                    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"].strip()
                else:
                    response = model.invoke(prompt)
                    content = response.content.strip()
                
                if content.startswith("```json"):
                    content = content[7:].rstrip("```").strip()
                
                page_data = json.loads(content)["page"]
                if page_data["Mot-clé principal unique"] in all_keywords:
                    page_data["Mot-clé principal unique"] += f" {len(all_keywords) + 1}"
                all_keywords.add(page_data["Mot-clé principal unique"])
                if page_data["Permalink"] in all_slugs:
                    page_data["Permalink"] += f"-{len(all_slugs) + 1}"
                all_slugs.add(page_data["Permalink"])
                enriched_pages.append(page_data)
                st.success(f"Page '{page_keyword}' enrichie avec succès.")
                progress_bar.progress(page_count / total_pages)
            except Exception as e:
                st.error(f"Erreur lors de l'enrichissement de '{page_keyword}' : {e}")
    
    st.success(f"Tableau enrichi généré avec succès ! Total pages enrichies : {len(enriched_pages)}")
    return {"pages": enriched_pages}

def generate_enriched_table_from_titles(titles, context, site_name, selected_api):
    st.info(f"Génération du tableau enrichi à partir des titres pour '{site_name}'")
    model = get_model(selected_api)
    if not model:
        return {"error": "API non disponible"}
    
    enriched_pages = []
    all_keywords = set()
    all_slugs = set()
    total_titles = len(titles)
    st.info(f"Nombre total de titres à enrichir : {total_titles}")
    progress_bar = st.progress(0)
    
    for idx, title in enumerate(titles, 1):
        st.info(f"Enrichissement du titre {idx}/{total_titles} : '{title}'")
        serp_urls = get_serpapi_results(title)
        serp_content = "".join([f"Contenu {url}:\n{fetch_page_content(url)[:1000]}\n\n" for url in serp_urls if "Erreur" not in fetch_page_content(url)])
        prompt = (
            f"Contexte '{site_name}': {context}. "
            f"Titre H1 : {title}. "
            f"Contenu SERP : {serp_content}. "
            "Générer tableau SEO 18 colonnes : Type de contenu, Titre H1 Page, Lien de parenté, Objectif, Mot-clé principal unique, "
            "Trafic estimé, Top 5 des SERP, Mots-clés secondaires, Intention utilisateur, Balise Title, Meta Description, Alt des images, "
            "EAAT, Liens principaux pour l’intro, Liens pages filles, Liens pages sœurs, Appels à l’action, Permalink, Statut de production. "
            "Retourne JSON : {'page': {colonne: valeur}}."
        )
        st.info(f"Envoi du prompt pour enrichir '{title}' (taille : {len(prompt)} caractères)")
        try:
            if selected_api == "Grok":
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"}
                data = {"messages": [{"role": "user", "content": prompt}], "model": "grok-2-latest", "stream": False, "temperature": 0}
                response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip()
            else:
                response = model.invoke(prompt)
                content = response.content.strip()
            
            if content.startswith("```json"):
                content = content[7:].rstrip("```").strip()
            
            page_data = json.loads(content)["page"]
            if page_data["Mot-clé principal unique"] in all_keywords:
                page_data["Mot-clé principal unique"] += f" {len(all_keywords) + 1}"
            all_keywords.add(page_data["Mot-clé principal unique"])
            if page_data["Permalink"] in all_slugs:
                page_data["Permalink"] += f"-{len(all_slugs) + 1}"
            all_slugs.add(page_data["Permalink"])
            enriched_pages.append(page_data)
            st.success(f"Titre '{title}' enrichi avec succès.")
            progress_bar.progress(idx / total_titles)
        except Exception as e:
            st.error(f"Erreur lors de l'enrichissement de '{title}' : {e}")
    
    st.success(f"Tableau enrichi généré avec succès ! Total titres enrichis : {len(enriched_pages)}")
    return {"pages": enriched_pages}