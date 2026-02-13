#Conexão com o banco Postgres
# app/db.py
import psycopg2
import streamlit as st

def conectar_banco():
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            dbname=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            port=st.secrets["DB_PORT"],
            connect_timeout=10
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: {e}")
        return None