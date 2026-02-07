import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from db import conectar_banco
from queries import QUERY_RESUMO_HOJE, QUERY_ATENDIMENTOS_HOJE
from dashboard_semanal import render_dashboard_semanal

st.set_page_config(
    page_title="Barbearia — Painel",
    layout="wide"
)

st.title("📊 Barbearia — Controle Diário")

# ===============================
# QR CODE PARA CLIENTES
# ===============================
st.subheader("📱 QR Code para atendimento")

# enquanto estiver local
url_formulario ="http://192.168.0.7:8501/Cliente"

qr = qrcode.make(url_formulario)
buf = BytesIO()
qr.save(buf, format="PNG")

st.image(
    buf.getvalue(),
    caption="Escaneie para registrar atendimento",
    width=250
)

st.divider()

# ===============================
# CONEXÃO COM BANCO
# ===============================
try:
    conn = conectar_banco()
    st.success("✅ Conectado ao banco de dados")
except Exception as e:
    st.error("❌ Erro ao conectar no banco")
    st.error(e)
    st.stop()

# ===============================
# RESUMO DO DIA
# ===============================
st.subheader("📅 Resumo de hoje")

df_resumo = pd.read_sql(QUERY_RESUMO_HOJE, conn)

col1, col2 = st.columns(2)
col1.metric("Atendimentos hoje", int(df_resumo.iloc[0, 0]))
col2.metric("Faturamento hoje (R$)", float(df_resumo.iloc[0, 1]))

# ===============================
# ATENDIMENTOS DO DIA
# ===============================
st.subheader("🧾 Atendimentos de hoje")

df_atendimentos = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
st.dataframe(df_atendimentos, use_container_width=True)

st.divider()
render_dashboard_semanal(conn) 