# --- QUERIES DE LOGIN E SEGURANÇA ---

QUERY_BUSCAR_CLIENTE_POR_CELULAR = """
SELECT id_cliente, COALESCE(nome, 'Cliente') as nome 
FROM public.cliente 
WHERE celular = %s LIMIT 1;
"""

QUERY_CHECAR_ATENDIMENTO_HOJE = """
SELECT EXISTS (
    SELECT 1 FROM public.atendimento 
    WHERE id_cliente = %s 
    AND (data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
        (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
);
"""

# --- QUERIES DE DASHBOARD ---

QUERY_RESUMO_HOJE = """
SELECT
    COUNT(a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas
FROM public.atendimento a
JOIN public.venda v ON v.id_venda = a.id_venda
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
      (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date;
"""

QUERY_RESUMO_SEMANA = """
SELECT
    DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') AS data,
    COUNT(a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas
FROM public.atendimento a
JOIN public.venda v ON v.id_venda = a.id_venda
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date >= 
      date_trunc('week', CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
GROUP BY DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
ORDER BY data;
"""

QUERY_ATENDIMENTOS_HOJE = """
SELECT
    TO_CHAR(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') AS horario,
    TRIM(COALESCE(c.nome, '') || ' ' || COALESCE(c.sobrenome, '')) AS cliente,
    COALESCE(c.celular, 'Sem Tel.') AS telefone,
    COALESCE(STRING_AGG(s.nome_servico, ', '), 'Serviço') AS servicos,
    COALESCE(v.total, 0) AS valor,
    COALESCE(v.caixinha, 0) AS Caixinhas,
    COALESCE(v.avaliacao, 0) AS nota
FROM public.atendimento a
JOIN public.cliente c ON c.id_cliente = a.id_cliente
JOIN public.venda v ON v.id_venda = a.id_venda
JOIN public.item_venda iv ON iv.id_venda = v.id_venda
JOIN public.servico s ON s.id_servico = iv.id_servico
WHERE (a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = 
      (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
GROUP BY a.id_atendimento, c.nome, c.sobrenome, c.celular, v.total, v.caixinha, v.avaliacao, a.data_atendimento
ORDER BY a.data_atendimento DESC;
"""

# --- QUERIES DE ESCRITA ---

QUERY_INSERT_VENDA = """
INSERT INTO public.venda (id_cliente, id_forma_pagamento, total, caixinha, avaliacao)
VALUES (%s, %s, %s, %s, %s) RETURNING id_venda;
"""

QUERY_INSERT_CLIENTE = """
INSERT INTO public.cliente (nome, celular) 
VALUES (%s, %s) 
RETURNING id_cliente;
"""

QUERY_INSERT_ITEM_VENDA = """
INSERT INTO public.item_venda (id_venda, id_servico, valor_unitario)
VALUES (%s, %s, %s);
"""

QUERY_INSERT_ATENDIMENTO = """
INSERT INTO public.atendimento (id_cliente, id_venda, observacao)
VALUES (%s, %s, %s);
"""

QUERY_RESUMO_MENSAL_GRAFICO = """
SELECT 
    DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') AS data,
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_servicos,
    COALESCE(SUM(v.caixinha), 0) AS total_caixinhas,
    COALESCE(AVG(v.avaliacao), 0) AS media_avaliacao
FROM public.atendimento a
JOIN public.venda v ON v.id_venda = a.id_venda
WHERE EXTRACT(MONTH FROM a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') = %s 
  AND EXTRACT(YEAR FROM a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo') = %s
GROUP BY DATE(a.data_atendimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')
ORDER BY data;
"""

QUERY_ATENDIMENTOS_POR_DATA = """
SELECT 
    TO_CHAR(v.data_venda AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') as "⏰ Hora",
    TRIM(COALESCE(c.nome, '') || ' ' || COALESCE(c.sobrenome, '')) as "👤 Cliente",
    COALESCE(c.celular, 'Sem Tel.') as "📱 Celular",
    COALESCE(s.nome_servico, 'Serviço') as "✂️ Corte",
    COALESCE(v.total, 0) as "💰 Valor",
    COALESCE(v.caixinha, 0) as "💸 Caixinha",
    COALESCE(v.avaliacao, 0) as "⭐ Nota"
FROM public.atendimento a
JOIN public.venda v ON a.id_venda = v.id_venda
JOIN public.cliente c ON a.id_cliente = c.id_cliente
JOIN public.item_venda iv ON v.id_venda = iv.id_venda
JOIN public.servico s ON iv.id_servico = s.id_servico
WHERE (v.data_venda AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo')::date = %s
ORDER BY v.data_venda ASC
"""