import sqlite3
import streamlit as st
import json
import csv

DB_PATH = "seo_generator.db"

def init_sqlite_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_structures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                structure TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enriched_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_data TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sitemap_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serp_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                result TEXT NOT NULL
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()

init_sqlite_db()

def store_structure_in_sqlite(structure):
    if not isinstance(structure, dict):
        st.error("Structure invalide.")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO site_structures (structure) VALUES (?)", (json.dumps(structure),))
        conn.commit()
        st.success("Structure enregistrée en base.")
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()

def store_enriched_pages_in_sqlite(enriched_data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for page in enriched_data["pages"]:
            cursor.execute("INSERT INTO enriched_pages (page_data) VALUES (?)", (json.dumps(page),))
        conn.commit()
        st.success("Pages enrichies enregistrées.")
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()

def store_sitemap_urls(urls):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for url in urls:
            cursor.execute("INSERT INTO sitemap_urls (url) VALUES (?)", (url,))
        conn.commit()
        st.success("URLs sitemap enregistrées.")
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()

def store_serp_results(keyword, urls):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for url in urls:
            cursor.execute("INSERT INTO serp_results (keyword, result) VALUES (?, ?)", (keyword, url))
        conn.commit()
        st.success("Résultats SERP enregistrés.")
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()

def load_structure_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT structure FROM site_structures ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
        return None
    finally:
        conn.close()

def load_enriched_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT page_data FROM enriched_pages")
        rows = cursor.fetchall()
        return {"pages": [json.loads(row[0]) for row in rows]} if rows else None
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
        return None
    finally:
        conn.close()

def load_sitemap_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM sitemap_urls")
        rows = cursor.fetchall()
        return [row[0] for row in rows] if rows else []
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
        return []
    finally:
        conn.close()

def load_serp_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT result FROM serp_results ORDER BY id ASC")
        rows = cursor.fetchall()
        return [row[0] for row in rows] if rows else []
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
        return []
    finally:
        conn.close()

def export_sitemap_from_db(filename="urls_sitemap.csv"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM sitemap_urls")
        rows = cursor.fetchall()
        if rows:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for row in rows:
                    writer.writerow([row[0]])
    except sqlite3.Error as e:
        st.error(f"Erreur export sitemap DB : {e}")
    finally:
        conn.close()

def export_serp_from_db(filename="serpapi_results.csv"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, result FROM serp_results")
        rows = cursor.fetchall()
        if rows:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["keyword", "result"])
                for row in rows:
                    writer.writerow(row)
    except sqlite3.Error as e:
        st.error(f"Erreur export SERP DB : {e}")
    finally:
        conn.close()
