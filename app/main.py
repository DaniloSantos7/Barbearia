import sys
from pathlib import Path
from io import BytesIO

import streamlit as st
import pandas as pd
import qrcode

sys.path.append(str(Path(__file__).parent))

from services.db import conectar_banco
from queries.atendimentos import (
    QUERY_RESUMO_HOJE,
    QUERY_RESUMO_SEMANA,
    QUERY_ATENDIMENTOS_HOJE
)

# -------------------------------
# CONFIGURAÇÃO
# -------------------------------
st.set_page_config(page_title="BarberDash", layout="wide", initial_sidebar_state="collapsed")

# Estilo para mobile
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
        /* Ajuste para títulos de seção */
        .chart-title { font-size: 1.2rem; font-weight: bold; margin-bottom: -20px; color: #555; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# LOGIN
# -------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        if senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# -------------------------------
# PROCESSAMENTO DE DADOS
# -------------------------------
conn = conectar_banco()

df_hoje_resumo = pd.read_sql(QUERY_RESUMO_HOJE, conn)
at_hoje = int(df_hoje_resumo["total_atendimentos"][0]) if not df_hoje_resumo.empty else 0
fat_hoje = float(df_hoje_resumo["faturamento"][0]) if not df_hoje_resumo.empty else 0.0

df_semana_resumo = pd.read_sql(QUERY_RESUMO_SEMANA, conn)
at_semana = int(df_semana_resumo["total_atendimentos"].sum())
fat_semana = float(df_semana_resumo["faturamento"].sum())

# -------------------------------
# INTERFACE PRINCIPAL
# -------------------------------
st.title("💈 BarberDash")

# Cards 2x2
c1, c2 = st.columns(2)
c1.metric("✂️ Hoje", at_hoje)
c2.metric("💰 Hoje", f"R$ {fat_hoje:.2f}")

c3, c4 = st.columns(2)
c3.metric("📅 Semana", at_semana)
c4.metric("💵 Semana", f"R$ {fat_semana:.2f}")

st.divider()

# Abas
tab_agenda, tab_graficos, tab_qr = st.tabs(["📋 Agenda", "📊 Evolução", "📱 QR Code"])

with tab_agenda:
    df_lista = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
    if df_lista.empty:
        st.info("Nenhum atendimento para hoje.")
    else:
        df_lista["horario"] = pd.to_datetime(df_lista["horario"]).dt.strftime("%H:%M")
        df_display = df_lista.rename(columns={
            "horario": "⏰", "cliente": "Cliente", 
            "servicos": "✂️", "valor": "R$"
        })
        st.dataframe(df_display[["⏰", "Cliente", "✂️", "R$"]], use_container_width=True, hide_index=True)

with tab_graficos:
    if not df_semana_resumo.empty:
        # Formata data e define como índice
        df_semana_resumo["data_fmt"] = pd.to_datetime(df_semana_resumo["data"]).dt.strftime("%d/%m")
        df_chart = df_semana_resumo.set_index("data_fmt")
        
        # Datas de início e fim para o título superior
        data_inicio = df_chart.index[0]
        data_fim = df_chart.index[-1]
        
        # Gráfico 1: Atendimentos
        st.markdown(f"**Período: {data_inicio} até {data_fim}**")
        st.markdown("### ✂️ Atendimentos Diários")
        st.bar_chart(df_chart["total_atendimentos"], color="#2980b9")
        
        st.divider()
        
        # Gráfico 2: Faturamento
        st.markdown("### 💰 Faturamento Diário")
        st.bar_chart(df_chart["faturamento"], color="#27ae60")
    else:
        st.info("Dados insuficientes para gráficos.")

with tab_qr:
    # --- AJUSTE QR CODE: Centralizado e menor ---
    url = "http://192.168.0.7:8501/formulario"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    
    # Criando colunas para centralizar e reduzir o tamanho
    # [1, 1, 1] cria 3 partes iguais. O QR Code fica na do meio (33% da tela)
    vies1, centro, vies2 = st.columns([1, 1.2, 1])
    with centro:
        st.image(buf.getvalue(), caption="Escaneie para agendar", use_container_width=True)
        st.code(url, language=None) # Link logo abaixo para cópia rápida

conn.close()