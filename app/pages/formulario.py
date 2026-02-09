import streamlit as st
import psycopg2
import base64
from pathlib import Path

# --------------------------------
# CONFIGURAÇÃO MOBILE
# --------------------------------
st.set_page_config(
    page_title="Barbearia",
    layout="centered"
)

# Função para converter imagem local para Base64 (necessário para HTML)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --------------------------------
# CONTROLE DE BALÕES
# --------------------------------
if "show_balloons" not in st.session_state:
    st.session_state.show_balloons = False

if st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False

# --------------------------------
# CONEXÃO
# --------------------------------
def get_connection():
    return psycopg2.connect(
        dbname="barbearia",
        user="postgres",
        password="211308",
        host="localhost",
        port="5432"
    )

# --------------------------------
# BUSCAR SERVIÇOS E PAGAMENTOS
# --------------------------------
def get_servicos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_formas_pagamento():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# --------------------------------
# TOPO PREMIUM (TRAVADO LADO A LADO)
# --------------------------------
# Carregando a imagem local para o HTML
img_path = "assets/barbeiro.gif"
if Path(img_path).exists():
    img_base64 = get_base64_of_bin_file(img_path)
    img_html = f'data:image/gif;base64,{img_base64}'
else:
    img_html = "" # Caso o arquivo não exista

st.markdown(
    f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 0;
        width: 100%;
    ">
        <img src="{img_html}" style="
            width: 120px; 
            height: 120px; 
            border-radius: 15px;
            object-fit: cover;
        ">
        <div style="flex-grow: 1;">
            <h3 style="
                margin: 0; 
                line-height: 1.1; 
                white-space: nowrap; 
                font-size: clamp(1.1rem, 5vw, 1.6rem);
            ">
                💈 Seja bem-vindo
            </h3>
            <h2 style="
                margin: 0; 
                line-height: 1.2; 
                white-space: nowrap; 
                font-weight: normal;
                font-size: clamp(0.8rem, 4vw, 1.1rem);
            ">
                ✅ Preencha as informações
            </h2>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --------------------------------
# FORMULÁRIO CLIENTE
# --------------------------------
nome = st.text_input("👤 Nome", placeholder="Seu nome", key="nome_cliente")

telefone = st.text_input("📱 Telefone", placeholder="Ex: 11987654321", max_chars=11, key="telefone_cliente")
telefone = "".join(filter(str.isdigit, telefone))

servicos = get_servicos()
formas = get_formas_pagamento()

servico_dict = {n: (i, p) for i, n, p in servicos}
forma_dict = {t: i for i, t in formas}

servicos_selecionados = st.multiselect("✂️ Serviços", options=list(servico_dict.keys()), key="servicos")

if servicos_selecionados:
    st.markdown("#### 🧾 Serviços selecionados")
    for s in servicos_selecionados:
        preco = servico_dict[s][1]
        st.markdown(f"- **{s}** — R$ {preco:.2f}")

forma_pagamento = st.selectbox("💳 Forma de pagamento", options=list(forma_dict.keys()), key="pagamento")

total = sum(servico_dict[s][1] for s in servicos_selecionados)
st.markdown(f"### 💰 Total: **R$ {total:.2f}**")

# --------------------------------
# SALVAR NO BANCO
# --------------------------------
if st.button("✅ Finalizar Atendimento", use_container_width=True):
    if not nome or not telefone or not servicos_selecionados:
        st.warning("Preencha todos os campos.")
    elif len(telefone) < 11:
        st.warning("O telefone deve ter no mínimo 11 dígitos (DDD + celular).")
    else:
        conn = get_connection()
        cur = conn.cursor()

        # Busca ou Insere Cliente
        cur.execute("SELECT id_cliente FROM cliente WHERE celular = %s", (telefone,))
        cliente = cur.fetchone()
        if cliente:
            id_cliente = cliente[0]
        else:
            cur.execute("INSERT INTO cliente (nome, celular) VALUES (%s, %s) RETURNING id_cliente", (nome, telefone))
            id_cliente = cur.fetchone()[0]

        # Venda
        cur.execute("INSERT INTO venda (total, id_cliente, id_forma_pagamento) VALUES (%s, %s, %s) RETURNING id_venda", 
                    (total, id_cliente, forma_dict[forma_pagamento]))
        id_venda = cur.fetchone()[0]

        # Itens e Atendimento
        for s in servicos_selecionados:
            id_servico, preco = servico_dict[s]
            cur.execute("INSERT INTO item_venda (id_venda, id_servico, valor_unitario) VALUES (%s, %s, %s)", (id_venda, id_servico, preco))
        
        cur.execute("INSERT INTO atendimento (id_cliente, id_venda) VALUES (%s, %s)", (id_cliente, id_venda))

        conn.commit()
        cur.close()
        conn.close()

        st.success("Atendimento registrado com sucesso! 💈🔥")
        st.session_state.show_balloons = True

        # Limpa formulário
        for key in ["nome_cliente", "telefone_cliente", "servicos", "pagamento"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()





