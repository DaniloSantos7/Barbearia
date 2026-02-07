import streamlit as st
import pandas as pd

from db import conectar_banco
from services.loaders import carregar_clientes, carregar_servicos, carregar_pagamentos
from services.cliente import cadastro_cliente
from services.atendimentos import formulario_atendimento

st.set_page_config(
    page_title="Atendimento - Barbearia",
    layout="centered"
)

st.title("✂️ Atendimento")
st.write("Preencha os dados abaixo para registrar seu atendimento.")

# ===============================
# CONEXÃO COM BANCO
# ===============================
try:
    conn = conectar_banco()
except Exception as e:
    st.error("Erro ao conectar no banco")
    st.stop()

# ===============================
# DADOS BASE
# ===============================
df_clientes = carregar_clientes(conn)
df_servicos = carregar_servicos(conn)
df_pagamentos = carregar_pagamentos(conn)

# ===============================
# CLIENTE
# ===============================
cadastro_cliente(conn)

st.divider()

# ===============================
# FORMULÁRIO DE ATENDIMENTO
# ===============================
formulario_atendimento(
    conn,
    df_clientes,
    df_servicos,
    df_pagamentos
)



