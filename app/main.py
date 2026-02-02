import streamlit as st
import pandas as pd

from db import conectar_banco
from queries import QUERY_RESUMO_HOJE, QUERY_ATENDIMENTOS_HOJE
from loaders import carregar_clientes, carregar_servicos, carregar_pagamentos
from app.cliente import cadastro_cliente
from atendimentos import formulario_atendimento

st.title("📊 Barbearia — Controle Diário")

# conexão
try:
    conn = conectar_banco()
    st.success("✅ Conectado ao banco de dados")
except Exception as e:
    st.error("❌ Erro ao conectar no banco")
    st.error(e)
    st.stop()

# resumo do dia
st.subheader("📅 Resumo de hoje")
df_resumo = pd.read_sql(QUERY_RESUMO_HOJE, conn)

col1, col2 = st.columns(2)
col1.metric("Atendimentos hoje", int(df_resumo.iloc[0, 0]))
col2.metric("Faturamento hoje (R$)", float(df_resumo.iloc[0, 1]))

# atendimentos do dia
st.subheader("🧾 Atendimentos de hoje")
df_atendimentos = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, conn)
st.dataframe(df_atendimentos)

# dados base
df_clientes = carregar_clientes(conn)
df_servicos = carregar_servicos(conn)
df_pagamentos = carregar_pagamentos(conn)

# UI
cadastro_cliente(conn)
formulario_atendimento(conn, df_clientes, df_servicos, df_pagamentos)
