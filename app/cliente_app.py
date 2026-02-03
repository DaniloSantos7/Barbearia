import streamlit as st 
import pandas as pd 
from db import conectar_banco
from cliente import cadastro_cliente

st.set_page_config(
    page_title="Registro de Atendimento",
    layout="centered"
)

st.title("✂️ Registro de Atendimento")

#conecta no banco
try:
    conn = conectar_banco()
    st.success("✅ Conectado ao banco de dados")
except Exception as e:
    st.error(...)
    st.stop()

#===============================
#CADASTRO RÁPIDO DO CLIENTE 
#===============================

cadastro_cliente(conn)

st.divider()

#=========================
#DADOS PARA O FORMULÁRIO
#=========================

df_clientes = pd.read_sql(
    "SELECT id_cliente, nome || ' ' || sobrenome AS nome FROM cliente ORDER BY nome",
    conn
)

df_servicos = pd.read_sql(
    "SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico",
    conn
)

df_pagamentos = pd.read_sql(
    "SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento ORDER BY tipo_pagamento",
    conn
)

opcoes_servicos = [
    (row.id_servico, f"{row.nome_servico} - R$ {row.preco:.2f}")
    for row in df_servicos.itertuples()
]

#===========================
#FORMULÁRIO DE ATENDIMENTO
#===========================

df_clientes = pd.read_sql(
    "SELECT id_cliente, nome || ' ' || sobrenome AS nome FROM cliente ORDER BY nome",
    conn
)

df_servicos = pd.read_sql(
    "SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico",
    conn
)

df_pagamentos = pd.read_sql(
    "SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento ORDER BY tipo_pagamento",
    conn
)

opcoes_servicos = [
    (row.id_servico, f"{row.nome_servico} - R$ {row.preco:.2f}")
    for row in df_servicos.itertuples()
]

#===============
#PROCESSAMENTO
#===============

st.subheader("🧾 Atendimento")

with st.form("form_atendimento_cliente"):

    cliente = st.selectbox(
        "Cliente",
        options=df_clientes["id_cliente"],
        format_func=lambda x: df_clientes.loc[
            df_clientes["id_cliente"] == x, "nome"
        ].values[0]
    )

    servicos = st.multiselect(
        "Serviços",
        options=opcoes_servicos,
        format_func=lambda x: x[1]
    )

    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        options=df_pagamentos["id_forma_pagamento"],
        format_func=lambda x: df_pagamentos.loc[
            df_pagamentos["id_forma_pagamento"] == x, "tipo_pagamento"
        ].values[0]
    )

    submit = st.form_submit_button("Registrar Atendimento")


