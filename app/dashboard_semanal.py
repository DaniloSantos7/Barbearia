import streamlit as st
import pandas as pd
from db import conectar_banco
from queries import (
    QUERY_RESUMO_SEMANAL,
    QUERY_FATURAMENTO_DIA,
    QUERY_SERVICOS_SEMANA
)

def render_dashboard_semanal(conn):
    st.subheader("📊 Resumo semanal")

    df_resumo = pd.read_sql(QUERY_RESUMO_SEMANAL, conn)

    col1, col2 = st.columns(2)
    col1.metric("Atendimentos na semana", int(df_resumo.iloc[0, 0]))
    col2.metric("Faturamento da semana (R$)", float(df_resumo.iloc[0, 1]))

    st.divider()

    st.subheader("📅 Faturamento por dia")
    df_dia = pd.read_sql(QUERY_FATURAMENTO_DIA, conn)
    st.bar_chart(df_dia.set_index("dia")["faturamento"])

    st.divider()

    st.subheader("✂️ Serviços mais vendidos")
    df_servicos = pd.read_sql(QUERY_SERVICOS_SEMANA, conn)
    st.dataframe(df_servicos, use_container_width=True)