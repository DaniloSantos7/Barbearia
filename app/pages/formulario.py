import streamlit as st
import psycopg2
from decimal import Decimal
import base64
from pathlib import Path
from queries.atendimentos import (
    QUERY_BUSCAR_CLIENTE_POR_CELULAR,
    QUERY_CHECAR_ATENDIMENTO_HOJE,
    QUERY_INSERT_VENDA,
    QUERY_INSERT_ITEM_VENDA,
    QUERY_INSERT_ATENDIMENTO,
    QUERY_INSERT_CLIENTE    
)
import pytz
from datetime import datetime

fuso_br = pytz.timezone('America/Sao_Paulo')

# --------------------------------
# CONFIGURAÇÃO E CSS DE SEGURANÇA
# --------------------------------
st.set_page_config(page_title="Barbearia", layout="centered")

# Esconde a sidebar e menus para o cliente não sair do formulário
st.markdown("""
    <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebar"], button[kind="header"] {
            display: none !important;
        }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        database=st.secrets["DB_NAME"]
    )

# --------------------------------
# ESTADOS DO FORMULÁRIO
# --------------------------------
if "step" not in st.session_state:
    st.session_state.step = "LOGIN"
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# --------------------------------
# FUNÇÕES DE APOIO
# --------------------------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def reset_form():
    for key in ["servicos", "pagamento", "caixinha", "avaliacao"]:
        if key in st.session_state: del st.session_state[key]
    st.session_state.step = "LOGIN"
    st.session_state.user_data = None

# --------------------------------
# TOPO PREMIUM
# --------------------------------
img_path = "assets/barbeiro.gif"
img_html = f'data:image/gif;base64,{get_base64_of_bin_file(img_path)}' if Path(img_path).exists() else ""

st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; padding: 10px 0;">
        <img src="{img_html}" style="width: 100px; height: 100px; border-radius: 15px; object-fit: cover;">
        <div>
            <h3 style="margin: 0;">💈 BarberFlow</h3>
            <p style="margin: 0; opacity: 0.8;">Atendimento por ordem de chegada</p>
        </div>
    </div>
""", unsafe_allow_html=True)
st.divider()

# --------------------------------
# FLUXO DO FORMULÁRIO (LOGIN -> CADASTRO -> FORM)
# --------------------------------
if st.session_state.step == "LOGIN":
    st.subheader("📱 Identifique-se")
    tel = st.text_input("Celular (DDD + Número)", max_chars=11, placeholder="11940028922")
    
    if st.button("Continuar", use_container_width=True):
        tel_clean = "".join(filter(str.isdigit, tel))
        if len(tel_clean) < 11:
            st.warning("Informe o número completo.")
        else:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(QUERY_BUSCAR_CLIENTE_POR_CELULAR, (tel_clean,))
            cliente = cur.fetchone()
            
            if cliente:
                id_cli, nome_cli = cliente
                cur.execute(QUERY_CHECAR_ATENDIMENTO_HOJE, (id_cli,))
                ja_foi = cur.fetchone()[0]
                
                if ja_foi:
                    st.error(f"📍 {nome_cli.split()[0]}, você já realizou um atendimento hoje. Até a próxima!")
                else:
                    st.session_state.user_data = {"id": id_cli, "nome": nome_cli, "celular": tel_clean}
                    st.session_state.step = "FORMULARIO"
                    st.rerun()
            else:
                st.session_state.temp_celular = tel_clean
                st.session_state.step = "CADASTRO"
                st.rerun()
            cur.close(); conn.close()

elif st.session_state.step == "CADASTRO":
    st.subheader("👋 Bem-vindo! Qual seu nome?")
    novo_nome = st.text_input("Nome Completo")
    if st.button("Finalizar Cadastro"):
        if novo_nome:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(QUERY_INSERT_CLIENTE, (novo_nome, st.session_state.temp_celular))
            id_novo = cur.fetchone()[0]
            conn.commit()
            st.session_state.user_data = {"id": id_novo, "nome": novo_nome}
            st.session_state.step = "FORMULARIO"
            cur.close(); conn.close()
            st.rerun()

elif st.session_state.step == "FORMULARIO":
    user = st.session_state.user_data
    st.success(f"Logado como: **{user['nome']}**")
    
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico")
    servico_dict = {n: (i, p) for i, n, p in cur.fetchall()}
    cur.execute("SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento")
    forma_dict = {t: i for i, t in cur.fetchall()}
    
    servicos_sel = st.multiselect("✂️ Serviços de hoje", options=list(servico_dict.keys()))
    forma_pgto = st.selectbox("💳 Pagamento", options=list(forma_dict.keys()))
    
    st.divider()
    st.write("### ✨ Opcionais")
    col1, col2 = st.columns(2)
    with col1:
        caixinha = st.number_input("💸 Caixinha", min_value=0.0, step=1.0)
    with col2:
        avaliacao = st.select_slider("⭐ Avaliação", options=[1, 2, 3, 4, 5], value=5)

    total = sum(servico_dict[s][1] for s in servicos_sel)
    st.markdown(f"## Total: R$ {total + Decimal(str(caixinha)):.2f}")

    if st.button("✅ Finalizar", use_container_width=True):
        if not servicos_sel:
            st.warning("Selecione ao menos um serviço.")
        else:
            cur.execute(QUERY_INSERT_VENDA, (user['id'], forma_dict[forma_pgto], total, caixinha, avaliacao))
            id_venda = cur.fetchone()[0]
            for s in servicos_sel:
                id_s, preco = servico_dict[s]
                cur.execute(QUERY_INSERT_ITEM_VENDA, (id_venda, id_s, preco))
            cur.execute(QUERY_INSERT_ATENDIMENTO, (user['id'], id_venda, ""))
            conn.commit(); cur.close(); conn.close()
            st.balloons()
            st.toast("Corte registrado!", icon='🔥')
            reset_form()
            st.rerun()

    if st.button("Sair / Trocar Usuário", type="secondary"):
        reset_form()
        st.rerun()

# --------------------------------
# PORTA DOS FUNDOS (ACESSO BARBEIRO)
# --------------------------------
st.markdown("<br><br><br>", unsafe_allow_html=True)
col_secret1, col_secret2 = st.columns([10, 1])

with col_secret2:
    if st.button("⚙️", help="Área Administrativa", key="btn_adm_secret"):
        st.session_state.show_admin_auth = True

if st.session_state.get("show_admin_auth"):
    st.divider()
    senha_adm = st.text_input("Senha Admin", type="password", key="input_adm_pwd")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Acessar Dashboard"):
            if senha_adm == "1234":
                st.switch_page("main.py")
            else:
                st.error("Senha incorreta")
    with c_btn2:
        if st.button("Fechar"):
            st.session_state.show_admin_auth = False
            st.rerun()




