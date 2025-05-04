import pandas as pd

def generate_markdown(structure):
    if not isinstance(structure, dict) or "error" in structure:
        return "# Erreur\nStructure invalide."
    markdown = "# Structure SEO\n\n## Structure du site\n\n"
    for category, data in structure.get("structure", {}).items():
        if not isinstance(data, dict) or "mot_cle_principal_unique" not in data:
            continue
        markdown += f"### {category}\n- **Mot-clé principal** : {data['mot_cle_principal_unique']}\n\n#### Pages\n"
        for page in data.get("pages", []):
            if isinstance(page, dict) and "mot_cle_principal_unique" in page:
                markdown += f"- **{page['type_page']}** : {page['mot_cle_principal_unique']}\n"
        markdown += "\n"
    return markdown

def generate_markdown_table(enriched_data):
    markdown = "# Tableau SEO Enrichi\n\n"
    markdown += "| Type de contenu | Titre H1 Page | Lien de parenté | Objectif | Mot-clé principal unique | Trafic estimé | Top 5 des SERP | Mots-clés secondaires | Intention utilisateur | Balise Title | Meta Description | Alt des images | EAAT | Liens principaux pour l’intro | Liens pages filles | Liens pages sœurs | Appels à l’action | Permalink | Statut de production |\n"
    markdown += "|-----------------|---------------|-----------------|----------|--------------------------|---------------|----------------|-----------------------|----------------------|--------------|------------------|----------------|------|-------------------------------|-------------------|-------------------|------------------|-----------|---------------------|\n"
    for page in enriched_data["pages"]:
        markdown += f"| {page['Type de contenu']} | {page['Titre H1 Page']} | {page['Lien de parenté']} | {page['Objectif']} | {page['Mot-clé principal unique']} | {page['Trafic estimé']} | {page['Top 5 des SERP']} | {page['Mots-clés secondaires']} | {page['Intention utilisateur']} | {page['Balise Title']} | {page['Meta Description']} | {page['Alt des images']} | {page['EAAT']} | {page['Liens principaux pour l’intro']} | {page['Liens pages filles']} | {page['Liens pages sœurs']} | {page['Appels à l’action']} | {page['Permalink']} | {page['Statut de production']} |\n"
    return markdown

def generate_csv(enriched_data):
    df = pd.DataFrame(enriched_data["pages"])
    return df.to_csv(index=False)