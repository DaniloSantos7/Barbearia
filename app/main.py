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
from sqlalchemy import create_engine, event
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from sqlalchemy.engine import URL
import locale
from dashboards.dashboard_semana import render_dashboard_semanal

# --- CONFIGURAÇÃO REGIONAL ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass 

# Ajuste de caminho e import das queries
sys.path.append(str(Path(__file__).parent))
from queries.atendimentos import *

# --- CONFIGURAÇÃO INICIAL ---
fuso_br = pytz.timezone('America/Sao_Paulo')
st_autorefresh(interval=120 * 1000, key="datarefresh")

# --- CONFIGURAÇÃO DA CONEXÃO ---
def get_engine():
    try:
        user = st.secrets["DB_USER"]
        password = st.secrets["DB_PASS"]
        host = st.secrets["DB_HOST"]
        port = int(st.secrets["DB_PORT"])
        dbname = st.secrets["DB_NAME"]

        connection_url = URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            query={"sslmode": "require", "options": "-c prepare_threshold=0"}
        )
        return create_engine(connection_url, pool_pre_ping=True, pool_recycle=300)
    except Exception as e:
        st.error(f"Erro ao configurar engine: {e}")
        return None

engine = get_engine()
df_h = pd.DataFrame()
df_s = pd.DataFrame()

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="BarberDash", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebar"], button[kind="header"] { display: none !important; }
        .block-container { padding-top: 1rem; }
        div[data-testid="stMetric"] { background-color: #1E1E1E; border: 1px solid #333; padding: 15px; border-radius: 12px; }
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

# --- BUSCA DE DADOS PRINCIPAL ---
if engine:
    try:
        with engine.connect() as conn:
            df_h = pd.read_sql(QUERY_RESUMO_HOJE, conn)
            df_s = pd.read_sql(QUERY_RESUMO_SEMANA, conn)
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")

# --- RESUMO DE HOJE ---
st.subheader("📍 Resumo de Hoje")
c1, c2, c3 = st.columns(3)
if not df_h.empty:
    fat_hoje = float(df_h["faturamento_servicos"].fillna(0).iloc[0])
    caixa_hoje = float(df_h["total_caixinhas"].fillna(0).iloc[0])
    c1.metric("✂️ Atendimentos", int(df_h["total_atendimentos"].fillna(0).iloc[0]))
    c2.metric("💰 Faturamento", f"R$ {fat_hoje:,.0f}".replace(',', '.'))
    c3.metric("💸 Caixinhas", f"R$ {caixa_hoje:,.0f}".replace(',', '.'))
else:
    c1.metric("✂️ Atendimentos", 0); c2.metric("💰 Faturamento", "R$ 0"); c3.metric("💸 Caixinhas", "R$ 0")

st.markdown("---")

# --- ABAS ---
t1, t2, t3, t4 = st.tabs(["📋 Agenda", "💰 Ganhos Semanais", "📊 Evolução Mensal", "📱 QR Cliente"])

with t1:
    st.write("### 📅 Consultar Agenda")
    data_consulta = st.date_input("Escolha o dia", value=datetime.now(fuso_br).date(), format="DD/MM/YYYY")

    if engine:
        try:
            with engine.connect() as conn:
                df_l = pd.read_sql(QUERY_ATENDIMENTOS_POR_DATA, conn, params=(data_consulta,))
            
            if not df_l.empty:
                total_dia = df_l["💰 Valor"].sum()
                st.metric("💵 Faturamento no Dia", f"R$ {total_dia:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                
                # Formatação Moeda BR
                for col in ["💰 Valor", "💸 Caixinha"]:
                    df_l[col] = df_l[col].map('R$ {:,.2f}'.format).str.replace('.', 'X').str.replace(',', '.').str.replace('X', ',')
                
                st.dataframe(df_l, use_container_width=True, hide_index=True)
            else:
                st.warning(f"Nenhum atendimento em {data_consulta.strftime('%d/%m/%Y')}.")
        except Exception as e:
            st.error(f"Erro ao carregar agenda: {e}")


with t2:
    if engine:
        try:
            with engine.connect() as conn:
                # 1. BUSCA DOS DADOS (Usando sua Query Real)
                df_semana = pd.read_sql(QUERY_RESUMO_SEMANA, conn)
                
                # 2. LÓGICA DE DATAS PARA A LEGENDA (Visual apenas)
                hoje = datetime.now(fuso_br)
                # Segunda-feira desta semana
                inicio_semana = (hoje - timedelta(days=hoje.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                # Domingo desta semana
                fim_semana = (inicio_semana + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=0)
                
                data_inicio_str = inicio_semana.strftime('%d/%m')
                data_fim_str = fim_semana.strftime('%d/%m')

                st.write(f"### 📅 Ciclo Semanal: {data_inicio_str} a {data_fim_str}")
                st.caption("Reset automático: Todo domingo às 23:59")

                if not df_semana.empty:
                    # --- CÁLCULOS ---
                    fat_sem = float(df_semana['faturamento_servicos'].sum())
                    caixa_sem = float(df_semana['total_caixinhas'].sum())
                    total_geral = fat_sem + caixa_sem

                    # --- MÉTRICAS COM EMOJIS ---
                    ms1, ms2, ms3 = st.columns(3)
                    ms1.metric("💰 Faturamento", f"R$ {fat_sem:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    ms2.metric("💸 Caixinhas", f"R$ {caixa_sem:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    ms3.metric("📈 Total Geral", f"R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                    st.divider()

                    # --- FORMATAÇÃO DO GRÁFICO ---
                    # Garante que a data está no formato datetime e cria a coluna formatada (Ex: 22/02)
                    df_semana['data'] = pd.to_datetime(df_semana['data'])
                    df_semana["data_grafico"] = df_semana["data"].dt.strftime("%d/%m")
                    
                    fig_sem = px.bar(
                        df_semana, 
                        x="data_grafico", 
                        y="faturamento_servicos",
                        title="Desempenho Diário (Serviços)",
                        template="plotly_dark",
                        
                    )
                    
                    fig_sem.update_traces(
                        marker_color='#ff4b4b', # Vermelho padrão
                        hovertemplate="<b>Data:</b> %{x}<br><b>Receita:</b> R$ %{y:,.2f}<extra></extra>"
                    )

                    # TRAVAMENTO TOTAL (MOBILE FRIENDLY)
                    fig_sem.update_layout(
                        dragmode=False, 
                        xaxis=dict(fixedrange=True, title=None), 
                        yaxis=dict(fixedrange=True, title=None),
                        bargap=0.3
                    )

                    st.plotly_chart(fig_sem, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info(f"Nenhum dado registrado para o ciclo {data_inicio_str} a {data_fim_str}.")

        except Exception as e:
            st.error(f"Erro ao carregar resumo semanal: {e}")

with t3:
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

    if engine:
        with engine.connect() as conn:
            df_m = pd.read_sql(QUERY_RESUMO_MENSAL_GRAFICO, conn, params=(mes_num, ano_num))

        if not df_m.empty:
            st.markdown(f"#### 📊 Acumulado de {mes_nome}")
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric("✂️ Cortes", int(df_m["total_atendimentos"].sum()))
            cm2.metric("💰 Serviços", f"R$ {df_m['faturamento_servicos'].sum():,.0f}".replace(',', '.'))
            cm3.metric("💸 Caixinhas", f"R$ {df_m['total_caixinhas'].sum():,.0f}".replace(',', '.'))
            cm4.metric("⭐ Avaliação", f"{df_m['media_avaliacao'].mean():.1f} / 5")
            
            st.divider()
            df_m["data_fmt"] = pd.to_datetime(df_m["data"]).dt.strftime("%d/%m")
            
            # Gráficos
            # --- GRÁFICO 1: VOLUME ---
            fig_vol = px.bar(
                df_m, x="data_fmt", y="total_atendimentos", 
                title="Volume de Clientes", template="plotly_dark",
                labels={"data_fmt": "Data", "total_atendimentos": "Clientes"}
            )
            fig_vol.update_traces(
                marker_color='#2980b9',
                hovertemplate="<b>Data:</b> %{x}<br><b>Clientes:</b> %{y}<extra></extra>"
            )
            fig_vol.update_layout(dragmode=False, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), bargap=0.3)
            st.plotly_chart(fig_vol, use_container_width=True, config={'displayModeBar': False})


            # --- GRÁFICO 2: FATURAMENTO ---
            fig_fat = px.bar(
                df_m, x="data_fmt", y="faturamento_servicos", 
                title="Receita de Serviços", template="plotly_dark",
                labels={"data_fmt": "Data", "faturamento_servicos": "Receita"}
            )
            fig_fat.update_traces(
                marker_color='#27ae60',
                hovertemplate="<b>Data:</b> %{x}<br><b>Receita:</b> R$ %{y:,.2f}<extra></extra>"
            )
            fig_fat.update_layout(dragmode=False, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), bargap=0.3)
            st.plotly_chart(fig_fat, use_container_width=True, config={'displayModeBar': False})

            # --- GRÁFICO 3: SATISFAÇÃO (ESTRELAS) ---
            fig_nota = px.line(
                df_m, x="data_fmt", y="media_avaliacao", 
                title="Evolução da Satisfação", template="plotly_dark", 
                markers=True,
                labels={"data_fmt": "Data", "media_avaliacao": "Nota Média"}
            )
            fig_nota.update_traces(
                line_color='#f1c40f',
                hovertemplate="<b>Data:</b> %{x}<br><b>Nota:</b> %{y:.1f} ⭐<extra></extra>"
            )
            fig_nota.update_layout(
                dragmode=False, 
                xaxis=dict(fixedrange=True), 
                yaxis=dict(range=[0, 5.1], fixedrange=True)
            )
            st.plotly_chart(fig_nota, use_container_width=True, config={'displayModeBar': False})
            
        else:
            st.warning("Sem dados para este período.")

with t4:
    st.write("### 🔗 Link do Tablet")
    url_cliente = "https://barbearia-flowokbfr5bqb9szv4txmp.streamlit.app/formulario"
    qr_img = qrcode.make(url_cliente)
    buf = BytesIO(); qr_img.save(buf, format="PNG")
    st.image(buf.getvalue(), width=250, caption="Aponte a câmera do Tablet aqui")
    st.code(url_cliente)