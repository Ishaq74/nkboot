import sqlite3
import streamlit as st
import json

DB_PATH = "seo_generator.db"

def init_sqlite_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS site_structures (id INTEGER PRIMARY KEY AUTOINCREMENT, structure TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS page_contents (id INTEGER PRIMARY KEY AUTOINCREMENT, page TEXT NOT NULL, url TEXT NOT NULL, content TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS enriched_pages (id INTEGER PRIMARY KEY AUTOINCREMENT, page_data TEXT NOT NULL)")
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
        st.success("Structure enregistrée.")
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
        st.success("Pages enregistrées.")
    except sqlite3.Error as e:
        st.error(f"Erreur SQLite : {e}")
    finally:
        conn.close()