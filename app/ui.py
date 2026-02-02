# Componentes de interface  (forms, dashboards)
# app/ui.py
import streamlit as st

def titulo():
    st.title("📊 Barbearia — Controle Diário")


def cadastro_cliente(conn, service_cadastrar):
    st.subheader("👤 Cliente")

    with st.expander("➕ Cadastrar novo cliente"):
        nome = st.text_input("Nome")
        sobrenome = st.text_input("Sobrenome")
        celular = st.text_input("Celular")

        if st.button("Salvar cliente"):
            if not nome or not celular:
                st.warning("Nome e celular são obrigatórios.")
            else:
                service_cadastrar(conn, nome, sobrenome, celular)
                st.success("✅ Cliente cadastrado!")
                st.rerun()