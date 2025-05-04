# Générateur de structure de site SEO

Ce projet est une application Streamlit avancée permettant de générer automatiquement une structure SEO complète pour un site web à partir de différentes sources d'entrées (SERP, sitemap, titres manuels), en utilisant des API LLM telles que Gemini, Anthropic ou Grok. Il est conçu pour fournir une pipeline SEO complète, avec étapes de sauvegarde, enrichissement, export et visualisation.

---

## 🚀 Fonctionnalités principales

* Recherche SERP via SerpAPI (avec gestion des exclusions de domaines).
* Exploration automatique de `robots.txt` et des fichiers sitemap (récursif).
* Enrichissement des pages avec IA (18 colonnes SEO).
* Choix du LLM utilisé : **Gemini**, **Anthropic Claude**, ou **Grok**.
* Sauvegarde à chaque étape en JSON / CSV local et dans **SQLite**.
* Rechargement possible à tout moment sans perte d'état.
* Export visuel et CSV de la table enrichie.
* Interface utilisateur claire avec boutons bien placés à chaque étape.

---

## 📂 Structure du projet

| Fichier            | Description                                                            |
| ------------------ | ---------------------------------------------------------------------- |
| `main.py`          | Interface utilisateur Streamlit, gère tout le processus.               |
| `utils.py`         | Scraping SERP, robots.txt, sitemap.xml, filtres, sauvegardes CSV/JSON. |
| `database.py`      | Connexion et manipulation de la base `seo_generator.db`.               |
| `ai_processing.py` | Interaction avec LLM pour structure et enrichissement.                 |
| `output.py`        | Génération de tableaux markdown et export CSV final.                   |
| `.env`             | Contient les clés API.                                                 |

---

## 🔧 Installation

### Prérequis

* Python 3.10 ou plus
* Créer un fichier `.env` à la racine :

```plaintext
SERPAPI_API_KEY=xxx
GEMINI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
GROK_API_KEY=xxx
```

### Dépendances Python

```bash
pip install streamlit requests beautifulsoup4 langchain langchain-google-genai langchain-anthropic python-dotenv serpapi
```

### Lancer l'application

```bash
streamlit run main.py
```

---

## 📊 Workflow global

1. **Choix du mode** : SERP, URLs manuelles, Titres H1
2. **Exploration sitemap** : depuis URLs ou robots.txt
3. **Génération IA de structure JSON**
4. **Validation ou édition manuelle JSON**
5. **Enrichissement IA (18 colonnes SEO)**
6. **Visualisation et export** : CSV + Markdown
7. **Sauvegarde automatique** à chaque étape (local & base de données)

---

## 📁 Base de données SQLite

Base : `seo_generator.db`

| Table             | Contenu                                |
| ----------------- | -------------------------------------- |
| `serp_results`    | URLs par mot-clé SERP                  |
| `sitemap_urls`    | Toutes les URLs extraites des sitemaps |
| `site_structures` | JSON structure IA générée              |
| `enriched_pages`  | Pages enrichies avec 18 colonnes SEO   |

---

## 📄 Format du tableau enrichi (18 colonnes)

| Colonne                  | Description                         |
| ------------------------ | ----------------------------------- |
| Type de contenu          | Page, article, produit...           |
| Titre H1 Page            | H1 optimisé                         |
| Lien de parenté          | Lien hiérarchique avec parent       |
| Objectif                 | Intention de la page                |
| Mot-clé principal unique | Unicité pour SEO                    |
| Trafic estimé            | Estimation via SERP                 |
| Top 5 des SERP           | Sites concurrents                   |
| Mots-clés secondaires    | Mots connexes                       |
| Intention utilisateur    | Informationnelle / transactionnelle |
| Balise Title             | Title tag optimisé                  |
| Meta Description         | Description engageante              |
| Alt des images           | Texte alternatif principal          |
| EEAT                     | Expertise / Autorité                |
| Liens intro              | Vers sites externes                 |
| Liens pages filles       | Pages internes descendantes         |
| Liens pages sœurs        | Pages du même niveau                |
| Appels à l’action        | Phrases incitatives                 |
| Permalink                | Slug optimisé                       |
| Statut de production     | Rédigé, à faire...                  |

---

## 📰 Export disponibles

* `serpapi_results.json`
* `urls_sitemap.csv`
* `structure_ia.json`
* `enriched_table.json`
* `enriched_pages.csv`
* Exports depuis la base (`database.py`)

---

## ✅ Objectif final

Fournir une **structure SEO enrichie, exploitable** pour :

* CMS (WordPress, Webflow\...)
* Générateurs statiques (Hugo, Astro, etc)
* Production d’articles / landing pages en masse

Chaque étape est **modulaire, documentée, sauvegardable** et réutilisable.

---

## 💪 Roadmap (prochaines étapes)

* [ ] Aperçu visuel sous forme de **mindmap (streamlit-markmap)**
* [ ] Edition directe des colonnes enrichies
* [ ] Intégration CMS automatique (export Hugo, etc)
* [ ] Rapport PDF par site (PDFKit / ReportLab)
* [ ] Mode multi-projets + dashboard

---

## 🚜 Support

En cas de bug, ouvre une issue ou contacte le développeur.

---

**Fait avec ♥ et GPT pour les professionnels du SEO.**
