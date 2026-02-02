import pandas as pd

def carregar_clientes(conn):
    return pd.read_sql(
        "SELECT id_cliente, nome || ' ' || sobrenome AS nome FROM cliente ORDER BY nome",
        conn
    )

def carregar_servicos(conn):
    return pd.read_sql(
        "SELECT id_servico, nome_servico, preco FROM servico ORDER BY nome_servico",
        conn
    )

def carregar_pagamentos(conn):
    return pd.read_sql(
        "SELECT id_forma_pagamento, tipo_pagamento FROM forma_pagamento ORDER BY tipo_pagamento",
        conn
    )