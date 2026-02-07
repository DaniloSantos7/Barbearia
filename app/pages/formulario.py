import streamlit as st
from services.db import conectar_banco

st.set_page_config(page_title="Registrar Atendimento", layout="centered")

st.title("✂️ Registrar atendimento")

cliente = st.text_input("Nome do cliente")
servico = st.selectbox(
    "Serviço",
    ["Corte", "Barba", "Corte + Barba"]
)
valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0)

if st.button("Salvar atendimento"):
    if not cliente:
        st.warning("Informe o nome do cliente.")
    else:
        conn = conectar_banco()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO atendimentos (cliente, servico, valor, data, horario)
            VALUES (%s, %s, %s, CURRENT_DATE, CURRENT_TIME)
            """,
            (cliente, servico, valor)
        )

        conn.commit()
        cur.close()
        conn.close()

        st.success("✅ Atendimento registrado com sucesso!")