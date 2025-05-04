import json
import os
import pandas as pd
import csv

def generate_markdown(structure):
    if not structure or "structure" not in structure:
        return "Aucune structure à afficher."
    
    md = "# Structure du site\n\n"
    for category, data in structure["structure"].items():
        md += f"## {category}\n"
        md += f"- Mot-clé principal : **{data.get('mot_cle_principal_unique', '')}**\n"
        for page in data.get("pages", []):
            type_page = page.get("type_page", "Inconnu")
            mot_cle = page.get("mot_cle_principal_unique", "")
            md += f"  - [{type_page}] {mot_cle}\n"
        md += "\n"
    return md

def generate_markdown_table(enriched_data):
    if not enriched_data or "pages" not in enriched_data:
        return "Aucune donnée enrichie disponible."
    
    pages = enriched_data["pages"]
    if not pages:
        return "Tableau vide."
    
    headers = list(pages[0].keys())
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    for row in pages:
        row_values = []
        for h in headers:
            value = str(row.get(h, "")).replace("\n", " ").replace("|", "\\|")
            row_values.append(value)
        md += "| " + " | ".join(row_values) + " |\n"
    return md

def generate_csv(enriched_data):
    if not enriched_data or "pages" not in enriched_data:
        return ""
    
    pages = enriched_data["pages"]
    if not pages:
        return ""
    
    headers = list(pages[0].keys())
    lines = [",".join(f'"{h}"' for h in headers)]
    for row in pages:
        line = []
        for h in headers:
            val = str(row.get(h, "")).replace('"', '""')
            line.append(f'"{val}"')
        lines.append(",".join(line))
    return "\n".join(lines)
