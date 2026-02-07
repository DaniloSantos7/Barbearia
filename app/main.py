import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO

from services.db import conectar_banco
from queries.atendimentos import (
    QUERY_RESUMO_HOJE,
    QUERY_ATENDIMENTOS_HOJE
)
from dashboards.dashboard_semanal import render_dashboard_semanal


st.set_page_config(
    page_title="Dashboard Barbearia",
    layout="wide"
)

st.title("📊 Dashboard da Barbearia")

# 🔌 Conexão
conn = conectar_banco()

# 📅 Resumo do dia
resumo = pd.read_sql(QUERY_RESUMO_HOJE, conn)

col1, col2 = st.columns(2)
col1.metric("Atendimentos hoje", int(resumo["total_atendimentos"][0]))
col2.metric("Faturamento hoje (R$)", resumo["faturamento_total"][0])

st.divider()

# 🧾 Atendimentos
df_atendimentos = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
st.dataframe(df_atendimentos, use_container_width=True)

st.divider()

# 📊 Dashboard semanal
render_dashboard_semanal(conn)

# 📱 QR Code
st.sidebar.subheader("📱 Formulário")

url_formulario = "http://localhost:8501/formulario"
qr = qrcode.make(url_formulario)

buf = BytesIO()
qr.save(buf, format="PNG")

st.sidebar.image(buf.getvalue(), caption="Escaneie para registrar atendimento")

conn.close()
