import streamlit as st
import pandas as pd
from queries.atendimentos import QUERY_RESUMO_SEMANA

def render_dashboard_semanal(conn):
    st.subheader("📆 Últimos 7 dias")

    df = pd.read_sql(QUERY_RESUMO_SEMANA, conn)

    if df.empty:
        st.info("Nenhum atendimento na última semana.")
        return

    df["data"] = pd.to_datetime(df["data"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✂️ Atendimentos")
        st.line_chart(df.set_index("data")["total_atendimentos"])

    with col2:
        st.markdown("### 💰 Faturamento")
        st.bar_chart(df.set_index("data")["faturamento"])