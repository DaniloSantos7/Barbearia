import streamlit as st

def cadastro_cliente(conn):
    st.subheader("👤 Cliente")

    with st.expander("➕ Cadastrar novo cliente"):
        nome = st.text_input("Nome")
        sobrenome = st.text_input("Sobrenome")
        celular = st.text_input("Celular")

        if st.button("Salvar cliente"):
            if not nome or not celular:
                st.warning("Nome e celular são obrigatórios.")
                return

            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO cliente (nome, sobrenome, celular)
                    VALUES (%s, %s, %s)
                    """,
                    (nome, sobrenome, celular)
                )
                conn.commit()
                st.success("✅ Cliente cadastrado!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(e)