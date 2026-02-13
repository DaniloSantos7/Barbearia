import sys
from pathlib import Path
from io import BytesIO
import datetime
from decimal import Decimal

import streamlit as st
import pandas as pd
import qrcode
import plotly.express as px

# Ajuste de caminho para imports
sys.path.append(str(Path(__file__).parent))

from services.db import conectar_banco
from queries.atendimentos import *

# -------------------------------
# CONFIGURAÇÃO E CSS
# -------------------------------
st.set_page_config(page_title="BarberDash", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        div[data-testid="stMetric"] {
            background-color: #1E1E1E;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 12px;
        }
        [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }
        [data-testid="stMetricLabel"] p { color: #BBBBBB !important; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
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

# --- CONEXÃO ---
conn = conectar_banco()

# --- INTERFACE PRINCIPAL ---
st.title("💈Barber Dash")

# KPIs de Hoje e Semana (Sempre visíveis)
df_h = pd.read_sql(QUERY_RESUMO_HOJE, conn)
df_s = pd.read_sql(QUERY_RESUMO_SEMANA, conn)

st.subheader("📍 Resumo de Hoje")
c1, c2 = st.columns(2)
c1.metric("✂️ Atendimentos", int(df_h["total_atendimentos"][0]) if not df_h.empty else 0)
c2.metric("💰 Faturamento", f"R$ {float(df_h['faturamento_servicos'][0]):.0f}" if not df_h.empty else "R$ 0")

st.markdown("---")

st.subheader("📅 Total da Semana")
c3, c4 = st.columns(2)
c3.metric("✂️ Quantidade Total", int(df_s["total_atendimentos"].sum()) if not df_s.empty else 0)
c4.metric("💵 Faturamento", f"R$ {df_s['faturamento'].sum():.0f}" if not df_s.empty else "R$ 0")

st.divider()

# ABAS
t1, t2, t3 = st.tabs(["📋 Agenda", "📊 Evolução Mensal", "📱 QR"])

with t1:
    df_l = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
    if not df_l.empty:
        df_l["horario"] = pd.to_datetime(df_l["horario"]).dt.strftime("%H:%M")
        st.dataframe(
            df_l.rename(columns={"horario":"⏰ horario","cliente":"nome","servicos":"✂️ corte","valor":"R$ valor"})[["⏰ horario","nome","✂️ corte","R$ valor"]], 
            use_container_width=True, 
            hide_index=True,
            column_config ={
                "R$ valor": st.column_config.NumberColumn(
                    "R$ valor",
                    format="R$ %.2f", #formata como Moeda Real com 2 casas decimais 
                )
            }
        )
    else:
        st.info("Nenhum atendimento agendado.")

with t2:
    st.write("### 🔍 Filtrar Período")
    
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    hoje = datetime.date.today()
    
    # Filtros
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nome = st.selectbox("Mês", list(meses_nomes.values()), index=hoje.month - 1)
        mes_num = [k for k, v in meses_nomes.items() if v == mes_nome][0]
    
    with col_ano:
        ano_atual = hoje.year
        lista_anos = list(range(ano_atual - 2, ano_atual + 1))
        ano_num = st.selectbox("Ano", lista_anos, index=len(lista_anos)-1)

    # Busca dados com o filtro aplicado
    df_m = pd.read_sql(QUERY_RESUMO_MENSAL_GRAFICO, conn, params=(mes_num, ano_num))

    if not df_m.empty:
        # --- TOTALIZADOR MENSAL ---
        total_at_mes = int(df_m["total_atendimentos"].sum())
        total_fat_mes = float(df_m["faturamento_servicos"].sum())

        st.markdown(f"#### 📊 Acumulado de {mes_nome}")
        cm1, cm2 = st.columns(2)
        cm1.metric("✂️ Total no Mês", total_at_mes)
        cm2.metric("💰 Total no Mês", f"R$ {total_fat_mes:.0f}")
        
        st.divider()

        # --- GRÁFICOS ---
        df_m["data_fmt"] = pd.to_datetime(df_m["data"]).dt.strftime("%d/%m")
        
        def criar_grafico_travado(df, y_col, titulo, cor):
            fig = px.bar(df, x="data_fmt", y=y_col, title=titulo)
            fig.update_traces(marker_color=cor)
            fig.update_layout(
                dragmode=False,
                xaxis={'fixedrange': False},
                yaxis={'fixedrange': True},
                height=300,
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=40, b=10)
            )
            return st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        criar_grafico_travado(df_m, "total_atendimentos", "Atendimentos por Dia", "#2980b9")
        st.write("") 
        criar_grafico_travado(df_m, "faturamento_servicos", "Faturamento por Dia", "#27ae60")
    else:
        st.warning(f"Nenhum registro encontrado para {mes_nome}/{ano_num}")

with t3:
    url = "http://192.168.0.7:8501/formulario"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=200)

conn.close()