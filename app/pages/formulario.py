import streamlit as st
import psycopg2

# --------------------------------
# CONFIGURAÇÃO MOBILE
# --------------------------------
st.set_page_config(
    page_title="Barbearia",
    layout="centered"
)

# --------------------------------
# CONTROLE DE BALÕES
# --------------------------------
if "show_balloons" not in st.session_state:
    st.session_state.show_balloons = False

# Mostra balões no ciclo correto
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
    cur.execute("""
        SELECT id_servico, nome_servico, preco
        FROM servico
        ORDER BY nome_servico
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_formas_pagamento():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_forma_pagamento, tipo_pagamento
        FROM forma_pagamento
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# --------------------------------
# TOPO PREMIUM (ALINHADO)
# --------------------------------
col1, col2 = st.columns([1, 4])

with col1:
    st.image("assets/barbeiro.gif", width=140)

with col2:
    st.markdown(
        """
        <div style="padding-top: 12px;">
            <h2 style="margin: 0; line-height: 1.1;">💈 Seja bem-vindo</h2>
            <div style="padding-top: 6px;">
                <h3 style="margin: 0; line-height: 1.1;">
                    ✅ Preencha as informações abaixo
                </h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --------------------------------
# FORMULÁRIO CLIENTE
# --------------------------------
nome = st.text_input(
    "👤 Nome",
    placeholder="Seu nome",
    key="nome_cliente"
)

telefone = st.text_input(
    "📱 Telefone",
    placeholder="Ex: 11987654321",
    max_chars=11,
    key="telefone_cliente"
)

# Garante somente números
telefone = "".join(filter(str.isdigit, telefone))

servicos = get_servicos()
formas = get_formas_pagamento()

# Dicionários
servico_dict = {
    nome_servico: (id_servico, preco)
    for id_servico, nome_servico, preco in servicos
}

forma_dict = {
    tipo: id_ for id_, tipo in formas
}

# --------------------------------
# SELEÇÃO DE SERVIÇOS
# --------------------------------
servicos_selecionados = st.multiselect(
    "✂️ Serviços",
    options=list(servico_dict.keys()),
    key="servicos"
)

# Mostra serviços selecionados (sem cortar texto)
if servicos_selecionados:
    st.markdown("#### 🧾 Serviços selecionados")
    for s in servicos_selecionados:
        preco = servico_dict[s][1]
        st.markdown(f"- **{s}** — R$ {preco:.2f}")

forma_pagamento = st.selectbox(
    "💳 Forma de pagamento",
    options=list(forma_dict.keys()),
    key="pagamento"
)

# Total
total = sum(servico_dict[s][1] for s in servicos_selecionados)
st.markdown(f"### 💰 Total: **R$ {total:.2f}**")

# --------------------------------
# SALVAR NO BANCO
# --------------------------------
if st.button("✅ Finalizar Atendimento", use_container_width=True):

    if not nome or not telefone or not servicos_selecionados:
        st.warning("Preencha todos os campos.")

    elif not telefone.isdigit():
        st.warning("O telefone deve conter apenas números.")

    elif len(telefone) < 11:
        st.warning("O telefone deve ter no mínimo 11 dígitos (DDD + celular).")

    else:
        conn = get_connection()
        cur = conn.cursor()

        # CLIENTE
        cur.execute(
            "SELECT id_cliente FROM cliente WHERE celular = %s",
            (telefone,)
        )
        cliente = cur.fetchone()

        if cliente:
            id_cliente = cliente[0]
        else:
            cur.execute(
                """
                INSERT INTO cliente (nome, celular)
                VALUES (%s, %s)
                RETURNING id_cliente
                """,
                (nome, telefone)
            )
            id_cliente = cur.fetchone()[0]

        # VENDA
        cur.execute(
            """
            INSERT INTO venda (total, id_cliente, id_forma_pagamento)
            VALUES (%s, %s, %s)
            RETURNING id_venda
            """,
            (total, id_cliente, forma_dict[forma_pagamento])
        )
        id_venda = cur.fetchone()[0]

        # ITEM_VENDA
        for s in servicos_selecionados:
            id_servico, preco = servico_dict[s]
            cur.execute(
                """
                INSERT INTO item_venda (id_venda, id_servico, valor_unitario)
                VALUES (%s, %s, %s)
                """,
                (id_venda, id_servico, preco)
            )

        # ATENDIMENTO
        cur.execute(
            """
            INSERT INTO atendimento (id_cliente, id_venda)
            VALUES (%s, %s)
            """,
            (id_cliente, id_venda)
        )

        conn.commit()
        cur.close()
        conn.close()

        st.success("Atendimento registrado com sucesso! 💈🔥")

        # Ativa balões no próximo ciclo
        st.session_state.show_balloons = True

        # Limpa formulário
        for key in ["nome_cliente", "telefone_cliente", "servicos", "pagamento"]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()





