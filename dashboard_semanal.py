import streamlit as st
import pandas as pd

def render_dashboard_semanal(conn):
    st.subheader("📊 Resumo semanal")

    query = """
    SELECT
        DATE(a.data_atendimento) AS dia,
        COUNT(*) AS atendimentos,
        SUM(v.total) AS faturamento
    FROM atendimento a
    JOIN venda v ON v.id_venda = a.id_venda
    WHERE a.data_atendimento >= CURRENT_DATE - INTERVAL '6 days'
    GROUP BY dia
    ORDER BY dia;
    """

    df = pd.read_sql(query, conn)

    st.line_chart(df.set_index("dia")["faturamento"])
    st.dataframe(df, use_container_width=True)
