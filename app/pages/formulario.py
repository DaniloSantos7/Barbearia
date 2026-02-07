import streamlit as st
import pandas as pd
from services.db import conectar_banco

st.set_page_config(
    page_title="Atendimento | Barbearia",
    layout="centered"
)

st.markdown("## ✂️ Novo Atendimento")
st.caption("Preencha rapidamente para registrar seu atendimento")

conn = conectar_banco()

# =========================
# DADOS BASE
# =========================
df_servicos = pd.read_sql(
    "SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico",
    conn
)

df_pagamentos = pd.read_sql(
    "SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento",
    conn
)

# =========================
# FORMULÁRIO
# =========================
with st.form("form_cliente", clear_on_submit=True):

    st.subheader("👤 Cliente")
    nome = st.text_input("Nome", placeholder="Seu nome")
    celular = st.text_input("Celular", placeholder="(99) 99999-9999")

    st.divider()

    st.subheader("💈 Serviço")
    servico_id = st.selectbox(
        "Escolha o serviço",
        options=df_servicos["id_servico"],
        format_func=lambda x: (
            f"{df_servicos.loc[df_servicos.id_servico == x, 'nome_servico'].values[0]} "
            f"- R$ {df_servicos.loc[df_servicos.id_servico == x, 'preco'].values[0]:.2f}"
        )
    )

    preco = float(
        df_servicos.loc[
            df_servicos["id_servico"] == servico_id, "preco"
        ].values[0]
    )

    st.info(f"💰 Valor do serviço: **R$ {preco:.2f}**")

    st.subheader("💳 Pagamento")
    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        options=df_pagamentos["id_forma_pagamento"],
        format_func=lambda x: df_pagamentos.loc[
            df_pagamentos.id_forma_pagamento == x, "tipo_pagamento"
        ].values[0]
    )

    st.markdown(f"### 🧾 Total: **R$ {preco:.2f}**")

    confirmar = st.form_submit_button("✅ Confirmar Atendimento")

# =========================
# SALVANDO NO BANCO
# =========================
if confirmar:
    if not nome or not celular:
        st.warning("Informe nome e celular.")
    else:
        try:
            cursor = conn.cursor()

            # cliente
            cursor.execute(
                """
                INSERT INTO cliente (nome, celular)
                VALUES (%s, %s)
                RETURNING id_cliente
                """,
                (nome, celular)
            )
            id_cliente = cursor.fetchone()[0]

            # venda
            cursor.execute(
                """
                INSERT INTO venda (id_cliente, id_forma_pagamento, total)
                VALUES (%s, %s, %s)
                RETURNING id_venda
                """,
                (id_cliente, forma_pagamento, preco)
            )
            id_venda = cursor.fetchone()[0]

            # item
            cursor.execute(
                """
                INSERT INTO item_venda (id_venda, id_servico, valor_unitario)
                VALUES (%s, %s, %s)
                """,
                (id_venda, servico_id, preco)
            )

            # atendimento
            cursor.execute(
                """
                INSERT INTO atendimento (id_cliente, id_venda)
                VALUES (%s, %s)
                """,
                (id_cliente, id_venda)
            )

            conn.commit()

            st.success("✅ Atendimento registrado com sucesso!")
            st.balloons()

        except Exception as e:
            conn.rollback()
            st.error("Erro ao registrar atendimento")
            st.error(e)






