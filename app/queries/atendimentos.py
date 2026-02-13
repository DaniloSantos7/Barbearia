# --- QUERIES DE LOGIN E SEGURANÇA (Alta Performance) ---

# Busca direta por índice (B-Tree)
QUERY_BUSCAR_CLIENTE_POR_CELULAR = """
SELECT id_cliente, nome FROM cliente WHERE celular = %s LIMIT 1;
"""

# Checagem de existência (mais rápido que COUNT)
QUERY_CHECAR_ATENDIMENTO_HOJE = """
SELECT EXISTS (
    SELECT 1 FROM atendimento 
    WHERE id_cliente = %s AND DATE(data_atendimento) = CURRENT_DATE
);
"""

# --- QUERIES DE ESCRITA (Novos Campos) ---

QUERY_INSERT_VENDA = """
INSERT INTO venda (id_cliente, id_forma_pagamento, total, caixinha, avaliacao)
VALUES (%s, %s, %s, %s, %s) RETURNING id_venda;
"""

# --- QUERIES DE DASHBOARD (Performance & Caixinha) ---

QUERY_RESUMO_HOJE = """
SELECT
    COUNT(id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE DATE(a.data_atendimento) = CURRENT_DATE;
"""

QUERY_RESUMO_SEMANA = """
SELECT
    DATE(a.data_atendimento) AS data,
    COUNT(a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos, -- Mudamos de 'faturamento' para 'faturamento_servicos'
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas    -- Mudamos de 'caixinhas' para 'total_caixinhas'
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE a.data_atendimento >= CURRENT_DATE - INTERVAL '6 days'
GROUP BY DATE(a.data_atendimento)
ORDER BY data;
"""

QUERY_ATENDIMENTOS_HOJE = """
SELECT
    TO_CHAR(a.data_atendimento, 'HH24:MI') AS horario,
    c.nome AS cliente,
    c.celular AS telefone, -- Coluna adicionada/garantida
    STRING_AGG(s.nome_servico, ', ') AS servicos,
    v.total AS valor,
    v.caixinha AS gorjeta,
    v.avaliacao AS nota
FROM atendimento a
JOIN cliente c ON c.id_cliente = a.id_cliente
JOIN venda v ON v.id_venda = a.id_venda
JOIN item_venda iv ON iv.id_venda = v.id_venda
JOIN servico s ON s.id_servico = iv.id_servico
WHERE DATE(a.data_atendimento) = CURRENT_DATE
GROUP BY a.id_atendimento, c.nome, c.celular, v.total, v.caixinha, v.avaliacao
ORDER BY a.data_atendimento DESC;
"""

# --- QUERIES DE INSERÇÃO QUE ESTAVAM FALTANDO ---

QUERY_INSERT_CLIENTE = """
INSERT INTO cliente (nome, celular) 
VALUES (%s, %s) 
RETURNING id_cliente;
"""

QUERY_INSERT_ITEM_VENDA = """
INSERT INTO item_venda (id_venda, id_servico, valor_unitario)
VALUES (%s, %s, %s);
"""

QUERY_INSERT_ATENDIMENTO = """
INSERT INTO atendimento (id_cliente, id_venda, observacao)
VALUES (%s, %s, %s);
"""

QUERY_RESUMO_MENSAL_GRAFICO = """
SELECT 
    DATE(a.data_atendimento) AS data,
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas,
    COALESCE(AVG(v.avaliacao), 0) AS media_avaliacao
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE EXTRACT(MONTH FROM a.data_atendimento) = %s 
  AND EXTRACT(YEAR FROM a.data_atendimento) = %s
GROUP BY DATE(a.data_atendimento)
ORDER BY data;"""