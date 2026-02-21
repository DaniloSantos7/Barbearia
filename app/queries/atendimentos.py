# --- QUERIES DE LOGIN E SEGURANÇA ---

QUERY_BUSCAR_CLIENTE_POR_CELULAR = """
SELECT id_cliente, nome FROM cliente WHERE celular = %s LIMIT 1;
"""

# Ajustado para considerar o fuso de Brasília ao checar duplicidade
QUERY_CHECAR_ATENDIMENTO_HOJE = """
SELECT EXISTS (
    SELECT 1 FROM atendimento 
    WHERE id_cliente = %s 
    AND (data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
        (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
);
"""

# --- QUERIES DE DASHBOARD ---

QUERY_RESUMO_HOJE = """
SELECT
    COUNT(id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
      (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date;
"""

QUERY_RESUMO_SEMANA = """
SELECT
    DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') AS data,
    COUNT(a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date >= 
      date_trunc('week', CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
GROUP BY DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
ORDER BY data;
"""

QUERY_ATENDIMENTOS_HOJE = """
SELECT
    TO_CHAR(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') AS horario,
    c.nome AS cliente,
    c.celular AS telefone,
    STRING_AGG(s.nome_servico, ', ') AS servicos,
    v.total AS valor,
    v.caixinha AS gorjeta,
    v.avaliacao AS nota
FROM atendimento a
JOIN cliente c ON c.id_cliente = a.id_cliente
JOIN venda v ON v.id_venda = a.id_venda
JOIN item_venda iv ON iv.id_venda = v.id_venda
JOIN servico s ON s.id_servico = iv.id_servico
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
      (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
GROUP BY a.id_atendimento, c.nome, c.celular, v.total, v.caixinha, v.avaliacao, a.data_atendimento
ORDER BY a.data_atendimento DESC;
"""

# --- QUERIES DE ESCRITA (Inalteradas, pois usam o Default do Banco ou timestamps completos) ---

QUERY_INSERT_VENDA = """
INSERT INTO venda (id_cliente, id_forma_pagamento, total, caixinha, avaliacao)
VALUES (%s, %s, %s, %s, %s) RETURNING id_venda;
"""

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
    DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') AS data,
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas,
    COALESCE(AVG(v.avaliacao), 0) AS media_avaliacao
FROM atendimento a
JOIN venda v ON v.id_venda = a.id_venda
WHERE EXTRACT(MONTH FROM a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') = %s 
  AND EXTRACT(YEAR FROM a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') = %s
GROUP BY DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
ORDER BY data;
"""

QUERY_ATENDIMENTOS_POR_DATA = """
    SELECT 
        v.data_venda::time as "⏰ Hora",
        c.nome || ' ' || c.sobrenome as "👤 Cliente",
        c.celular as "📱 Celular",
        s.nome_servico as "✂️ Corte",
        v.total as "💰 Valor",
        v.caixinha as "💸 Gorjeta",
        v.avaliacao as "⭐ Nota"
    FROM public.atendimento a
    JOIN public.venda v ON a.id_venda = v.id_venda
    JOIN public.cliente c ON a.id_cliente = c.id_cliente
    JOIN public.item_venda iv ON v.id_venda = iv.id_venda
    JOIN public.servico s ON iv.id_servico = s.id_servico
    WHERE v.data_venda::date = %s
    ORDER BY v.data_venda ASC
"""