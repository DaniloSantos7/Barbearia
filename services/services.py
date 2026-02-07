#Regras de negócio (insert, cálculos)
#tudo que insere , calcula ou processa dados 
# app/services.py
import pandas as pd

def cadastrar_cliente(conn, nome, sobrenome, celular):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO cliente (nome, sobrenome, celular)
        VALUES (%s, %s, %s)
        """,
        (nome, sobrenome, celular)
    )
    conn.commit()


def calcular_total(df_servicos, ids_servicos):
    return float(
        df_servicos[
            df_servicos["id_servico"].isin(ids_servicos)
        ]["preco"].sum()
    )


def registrar_atendimento(conn, cliente, forma_pagamento, ids_servicos, df_servicos):
    cursor = conn.cursor()

    total = calcular_total(df_servicos, ids_servicos)

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
    return total