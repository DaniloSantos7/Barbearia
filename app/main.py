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
        /* Esconde navegação lateral para o cliente não ver as abas */
        [data-testid="stSidebarNav"], [data-testid="stSidebar"], button[kind="header"] {
            display: none !important;
        }
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
    st.title("🔐 Painel Administrativo")
    senha = st.text_input("Senha do Barbeiro", type="password")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        if st.button("Entrar", use_container_width=True):
            if senha == "1234":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    with col_l2:
        if st.button("Voltar ao Formulário", use_container_width=True):
            st.switch_page("pages/formulario.py")
    st.stop()   

# --- CONEXÃO ---
conn = conectar_banco()

# --- INTERFACE PRINCIPAL ---
header_col1, header_col2 = st.columns([9, 1])
with header_col1:
    st.title("💈 Barber Dash")
with header_col2:
    if st.button("Sair"):
        st.session_state.logado = False
        st.switch_page("pages/formulario.py")

# --- BUSCA DE DADOS ---
df_h = pd.read_sql(QUERY_RESUMO_HOJE, conn)
df_s = pd.read_sql(QUERY_RESUMO_SEMANA, conn)

# --- RESUMO DE HOJE ---
st.subheader("📍 Resumo de Hoje")
c1, c2, c3 = st.columns(3)
if not df_h.empty:
    fat_hoje = float(df_h["faturamento_servicos"].fillna(0)[0])
    caixa_hoje = float(df_h["total_caixinhas"].fillna(0)[0])
    c1.metric("✂️ Atendimentos", int(df_h["total_atendimentos"].fillna(0)[0]))
    c2.metric("💰 Faturamento", f"R$ {fat_hoje:.0f}")
    c3.metric("💸 Caixinhas", f"R$ {caixa_hoje:.0f}")
else:
    c1.metric("✂️ Atendimentos", 0)
    c2.metric("💰 Faturamento", "R$ 0")
    c3.metric("💸 Caixinhas", "R$ 0")

st.markdown("---")

# --- TOTAL DA SEMANA ---
st.subheader("📅 Total da Semana")
c3_s, c4_s = st.columns(2)
if not df_s.empty:
    qtd_semana = int(df_s["total_atendimentos"].sum())
    # Correção do bug: faturamento_servicos em vez de faturamento
    fat_semana = float(df_s["faturamento_servicos"].sum())
    c3_s.metric("✂️ Quantidade Total", qtd_semana)
    c4_s.metric("💵 Faturamento", f"R$ {fat_semana:.0f}")
else:
    c3_s.metric("✂️ Quantidade Total", 0)
    c4_s.metric("💵 Faturamento", "R$ 0")

st.divider()

# --- ABAS ---
t1, t2, t3 = st.tabs(["📋 Agenda", "📊 Evolução Mensal", "📱 QR Cliente"])

with t1:
    df_l = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
    if not df_l.empty:
        df_display = df_l.rename(columns={
            "horario": "⏰ Hora", "cliente": "👤 Cliente", "telefone": "📱 Celular",
            "servicos": "✂️ Corte", "valor": "💰 Valor", "gorjeta": "💸 Gorjeta", "nota": "⭐ Nota"
        })
        st.dataframe(
            df_display[["⏰ Hora", "👤 Cliente", "📱 Celular", "✂️ Corte", "💰 Valor", "💸 Gorjeta", "⭐ Nota"]], 
            use_container_width=True, hide_index=True,
            column_config={
                "💰 Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                "💸 Gorjeta": st.column_config.NumberColumn(format="R$ %.2f"),
                "⭐ Nota": st.column_config.NumberColumn(format="%d ⭐")
            }
        )
    else:
        st.info("Nenhum atendimento registrado hoje.")
    
with t2:
    st.write("### 🔍 Filtrar Período")
    hoje = datetime.date.today()
    meses_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                   7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nome = st.selectbox("Mês", list(meses_nomes.values()), index=hoje.month - 1)
        mes_num = [k for k, v in meses_nomes.items() if v == mes_nome][0]
    with col_ano:
        ano_num = st.selectbox("Ano", list(range(hoje.year - 1, hoje.year + 1)), index=1)

    df_m = pd.read_sql(QUERY_RESUMO_MENSAL_GRAFICO, conn, params=(mes_num, ano_num))

    if not df_m.empty:
        total_at_mes = int(df_m["total_atendimentos"].sum())
        total_fat_mes = float(df_m["faturamento_servicos"].sum())
        total_cax_mes = float(df_m["total_caixinhas"].sum())

        st.markdown(f"#### 📊 Acumulado de {mes_nome}")
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric("✂️ Cortes", total_at_mes)
        cm2.metric("💰 Serviços", f"R$ {total_fat_mes:.0f}")
        cm3.metric("💸 Gorjetas", f"R$ {total_cax_mes:.0f}")
        
        st.divider()
        df_m["data_fmt"] = pd.to_datetime(df_m["data"]).dt.strftime("%d/%m")
        
        # FUNÇÃO DE GRÁFICO TRAVADO (Sem Zoom/Scroll)
        def criar_grafico_congelado(df, y_col, titulo, cor):
            fig = px.bar(df, x="data_fmt", y=y_col, title=titulo, template="plotly_dark")
            fig.update_traces(marker_color=cor)
            fig.update_layout(
                height=300,
                dragmode=False, # Trava o mouse
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(fixedrange=True), # Trava zoom no X
                yaxis=dict(fixedrange=True)  # Trava zoom no Y
            )
            return st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        criar_grafico_congelado(df_m, "total_atendimentos", "Volume de Clientes", "#2980b9")
        st.write("")
        criar_grafico_congelado(df_m, "faturamento_servicos", "Receita de Serviços", "#27ae60")
    else:
        st.warning("Sem dados para este período.")

with t3:
    st.write("### 🔗 Link do Tablet")
    url_cliente = "http://Barbearia.streamlit.app/formulario"
    qr = qrcode.make(url_cliente)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=250, caption="Aponte a câmera do Tablet aqui")
    st.code(url_cliente)

conn.close()