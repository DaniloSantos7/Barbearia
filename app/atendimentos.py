import streamlit as st

def formulario_atendimento(conn, df_clientes, df_servicos, df_pagamentos):
    st.subheader("✂️ Novo Atendimento")

    opcoes_servicos = [
        (row.id_servico, f"{row.nome_servico} - R$ {row.preco:.2f}")
        for row in df_servicos.itertuples()
    ]

    with st.form("form_atendimento"):
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

    if not submit:
        return

    if not servicos:
        st.warning("Selecione pelo menos um serviço.")
        return

    ids_servicos = [s[0] for s in servicos]

    total = float(
        df_servicos[
            df_servicos["id_servico"].isin(ids_servicos)
        ]["preco"].sum()
    )

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO venda (id_cliente, id_forma_pagamento, total)
            VALUES (%s, %s, %s)
            RETURNING id_venda;
            """,
            (cliente, forma_pagamento, total)
        )
        id_venda = cursor.fetchone()[0]

        for id_servico in ids_servicos:
            preco = float(
                df_servicos.loc[
                    df_servicos["id_servico"] == id_servico, "preco"
                ].values[0]
            )

            cursor.execute(
                """
                INSERT INTO item_venda (id_venda, id_servico, valor_unitario)
                VALUES (%s, %s, %s);
                """,
                (id_venda, id_servico, preco)
            )

        cursor.execute(
            """
            INSERT INTO atendimento (id_cliente, id_venda)
            VALUES (%s, %s);
            """,
            (cliente, id_venda)
        )

        conn.commit()
        st.success(f"✅ Atendimento registrado! Total: R$ {total:.2f}")
        st.rerun()

    except Exception as e:
        conn.rollback()
        st.error("❌ Erro ao registrar atendimento")
        st.error(e)