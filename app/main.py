import sys
from pathlib import Path
from io import BytesIO
import datetime
import urllib.parse
import pytz
import streamlit as st
import pandas as pd
import qrcode
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event

# --- CONFIGURAÇÃO INICIAL ---
fuso_br = pytz.timezone('America/Sao_Paulo')

# Atualiza o app automaticamente a cada 120 segundos (2 minutos)
st_autorefresh(interval=120 * 1000, key="datarefresh")

# --- CONFIGURAÇÃO DA CONEXÃO (SQLAlchemy) ---
def get_engine():
    user = st.secrets["DB_USER"]
    password = urllib.parse.quote_plus(st.secrets["DB_PASS"])
    host = st.secrets["DB_HOST"]
    port = st.secrets["DB_PORT"]
    dbname = st.secrets["DB_NAME"]
    
    # Montamos a URL com o parâmetro de forma direta e limpa
    # O ?sslmode=require é essencial para o Streamlit Cloud
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300
    )
    

    @event.listens_for(engine, "connect")
    def set_prepare_threshold(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET prepare_threshold = 0")
        cursor.close()
    
    return engine

engine = get_engine()

# Ajuste de caminho para imports
sys.path.append(str(Path(__file__).parent))
from queries.atendimentos import *

# --- CONFIGURAÇÃO E CSS ---
st.set_page_config(page_title="BarberDash", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
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
        if st.button("Entrar", width="stretch"):
            if senha == "1234":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    with col_l2:
        if st.button("Voltar ao Formulário", width="stretch"):
            st.switch_page("pages/formulario.py")
    st.stop()   

# --- INTERFACE PRINCIPAL ---
header_col1, header_col2, header_col3 = st.columns([7, 2, 1])
with header_col1:
    st.title("💈 Barber Dash")
with header_col2:
    if st.button("🔄 Atualizar Agora"):
        st.cache_data.clear()
        st.rerun()
with header_col3:
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# --- BUSCA DE DADOS ---
# Nota: Removido cache manual para garantir que o autorefresh pegue dados reais
df_h = pd.read_sql(QUERY_RESUMO_HOJE, engine)
df_s = pd.read_sql(QUERY_RESUMO_SEMANA, engine)

# --- RESUMO DE HOJE ---
st.subheader("📍 Resumo de Hoje")
c1, c2, c3 = st.columns(3)
if not df_h.empty:
    fat_hoje = float(df_h["faturamento_servicos"].fillna(0).iloc[0])
    caixa_hoje = float(df_h["total_caixinhas"].fillna(0).iloc[0])
    c1.metric("✂️ Atendimentos", int(df_h["total_atendimentos"].fillna(0).iloc[0]))
    c2.metric("💰 Faturamento", f"R$ {fat_hoje:.0f}")
    c3.metric("💸 Caixinhas", f"R$ {caixa_hoje:.0f}")
else:
    c1.metric("✂️ Atendimentos", 0)
    c2.metric("💰 Faturamento", "R$ 0")
    c3.metric("💸 Caixinhas", "R$ 0")

st.markdown("---")

# --- TOTAL DA SEMANA ---
# --- TOTAL DA SEMANA ---
st.subheader("📅 Total da Semana")

# Cálculo para mostrar as datas da semana atual (Segunda a Domingo)
hoje_datetime = datetime.now(fuso_br)
# .weekday() retorna 0 para segunda, 1 para terça...
inicio_semana = hoje_datetime - timedelta(days=hoje_datetime.weekday())
fim_semana = inicio_semana + timedelta(days=6)

st.markdown(f"*{inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')} (Reseta toda segunda-feira)*")

c3_s, c4_s = st.columns(2)
if not df_s.empty:
    qtd_semana = int(df_s["total_atendimentos"].sum())
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
    df_l = pd.read_sql(QUERY_ATENDIMENTOS_HOJE, engine)
    if not df_l.empty:
        df_display = df_l.rename(columns={
            "horario": "⏰ Hora", "cliente": "👤 Cliente", "telefone": "📱 Celular",
            "servicos": "✂️ Corte", "valor": "💰 Valor", "gorjeta": "💸 Gorjeta", "nota": "⭐ Nota"
        })
        st.dataframe(
            df_display[["⏰ Hora", "👤 Cliente", "📱 Celular", "✂️ Corte", "💰 Valor", "💸 Gorjeta", "⭐ Nota"]], 
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhum atendimento registrado hoje.")
    
with t2:
    st.write("### 🔍 Filtrar Período")
    hoje_data = datetime.now(fuso_br).date()
    meses_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                   7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    
    col_mes, col_ano = st.columns(2)
    with col_mes:
        mes_nome = st.selectbox("Mês", list(meses_nomes.values()), index=hoje_data.month - 1)
        mes_num = [k for k, v in meses_nomes.items() if v == mes_nome][0]
    with col_ano:
        ano_num = st.selectbox("Ano", list(range(hoje_data.year - 1, hoje_data.year + 1)), index=1)

    df_m = pd.read_sql(QUERY_RESUMO_MENSAL_GRAFICO, engine, params=(mes_num, ano_num))

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
        
        def criar_grafico_congelado(df, y_col, titulo, cor):
            fig = px.bar(df, x="data_fmt", y=y_col, title=titulo, template="plotly_dark")
            fig.update_traces(marker_color=cor)
            fig.update_layout(height=300, dragmode=False, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True))
            return st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        criar_grafico_congelado(df_m, "total_atendimentos", "Volume de Clientes", "#2980b9")
        criar_grafico_congelado(df_m, "faturamento_servicos", "Receita de Serviços", "#27ae60")
    else:
        st.warning("Sem dados para este período.")

with t3:
    st.write("### 🔗 Link do Tablet")
    url_cliente = "https://barbearia-flowokbfr5bqb9szv4txmp.streamlit.app/formulario"
    
    @st.cache_resource
    def gerar_qr_code(url):
        qr = qrcode.make(url)
        buf = BytesIO()
        qr.save(buf, format="PNG") 
        return buf.getvalue()

    qr_img = gerar_qr_code(url_cliente)
    st.image(qr_img, width=250, caption="Aponte a câmera do Tablet aqui")
    st.code(url_cliente)