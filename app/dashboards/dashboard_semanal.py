import streamlit as st
import pandas as pd
from queries.atendimentos import QUERY_SEMANAL


def render_dashboard_semanal(conn):
    st.subheader("📈 Desempenho semanal")

    df = pd.read_sql(QUERY_SEMANAL, conn)

    if df.empty:
        st.info("Nenhum atendimento registrado na última semana.")
        return

    df["data"] = pd.to_datetime(df["data"])

    # 📊 Atendimentos por dia
    st.markdown("### ✂️ Atendimentos")
    st.line_chart(
        df.set_index("data")["total_atendimentos"]
    )

    # 💰 Faturamento por dia
    st.markdown("### 💰 Faturamento (R$)")
    st.bar_chart(
        df.set_index("data")["faturamento"]
    )