QUERY_RESUMO_HOJE = """
SELECT
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento
FROM atendimento a
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE DATE(a.data_atendimento) = CURRENT_DATE;
"""

QUERY_RESUMO_SEMANA = """
SELECT
    DATE(a.data_atendimento) AS data,
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento
FROM atendimento a
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE a.data_atendimento >= CURRENT_DATE - INTERVAL '6 days'
GROUP BY DATE(a.data_atendimento)
ORDER BY data;
"""

QUERY_ATENDIMENTOS_HOJE = """
SELECT
    a.data_atendimento AS horario,
    c.nome AS cliente,
    c.celular AS telefone,
    STRING_AGG(s.nome_servico, ', ') AS servicos,
    fp.tipo_pagamento AS pagamento,
    v.total AS valor
FROM atendimento a
JOIN cliente c ON c.id_cliente = a.id_cliente
LEFT JOIN venda v ON v.id_venda = a.id_venda
LEFT JOIN forma_pagamento fp ON fp.id_forma_pagamento = v.id_forma_pagamento
LEFT JOIN item_venda iv ON iv.id_venda = v.id_venda
LEFT JOIN servico s ON s.id_servico = iv.id_servico
WHERE DATE(a.data_atendimento) = CURRENT_DATE
GROUP BY
    a.data_atendimento,
    c.nome,
    c.celular,
    fp.tipo_pagamento,
    v.total
ORDER BY horario DESC;
"""
