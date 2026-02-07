#Conexão com o banco Postgres
# app/db.py
import streamlit as st
import psycopg2

def conectar_banco():
    return psycopg2.connect(
        host=st.secrets["connections"]["barbearia_db"]["host"],
        port=st.secrets["connections"]["barbearia_db"]["port"],
        database=st.secrets["connections"]["barbearia_db"]["database"],
        user=st.secrets["connections"]["barbearia_db"]["username"],
        password=st.secrets["connections"]["barbearia_db"]["password"]
    )