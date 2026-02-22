import streamlit as st
import pandas as pd
import plotly.express as px
from queries.atendimentos import QUERY_RESUMO_SEMANA

def render_dashboard_semanal(conn):
    st.subheader("💰 Performance da Semana")
    st.caption("Ciclo: Segunda a Domingo (Reset automático à 00h de Segunda)")

    df = pd.read_sql(QUERY_RESUMO_SEMANA, conn)

    if df.empty:
        st.info("Nenhum atendimento registrado nesta semana ainda.")
        return

    df["data"] = pd.to_datetime(df["data"])
    
    # Cálculo de totais para os cards
    total_faturamento = df["faturamento_servicos"].sum()
    total_caixinhas = df["total_caixinhas"].sum()
    total_geral = total_faturamento + total_caixinhas

    # Métricas em destaque
    m1, m2, m3 = st.columns(3)
    m1.metric("Faturamento", f"R$ {total_faturamento:,.2f}")
    m2.metric("Caixinhas", f"R$ {total_caixinhas:,.2f}")
    m3.metric("Total Geral", f"R$ {total_geral:,.2f}")

    st.divider()

    # Gráfico de Barras Empilhadas (Serviços + Caixinhas)
    # Transformamos o DF para um formato que o Plotly entenda melhor para empilhar
    df_melted = df.melt(id_vars=['data'], value_vars=['faturamento_servicos', 'total_caixinhas'],
                        var_name='Tipo', value_name='Valor')
    
    fig = px.bar(df_melted, x='data', y='Valor', color='Tipo',
                 title="Evolução Diária (Faturamento + Caixinhas)",
                 color_discrete_map={'faturamento_servicos': '#ff4b4b', 'total_caixinhas': '#ffa500'},
                 barmode='stack')
    
    fig.update_layout(xaxis_title="Dia", yaxis_title="Valor (R$)", legend_title="Legenda")
    
    st.plotly_chart(fig, use_container_width=True)