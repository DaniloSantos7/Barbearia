QUERY_RESUMO_HOJE = """
SELECT
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_total
FROM atendimento a
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE DATE(a.data_atendimento) = CURRENT_DATE;
"""

QUERY_ATENDIMENTOS_HOJE = """
SELECT
    a.id_atendimento,
    c.nome || ' ' || c.sobrenome AS cliente,
    a.data_atendimento,
    v.total
FROM atendimento a
JOIN cliente c ON c.id_cliente = a.id_cliente
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE DATE(a.data_atendimento) = CURRENT_DATE
ORDER BY a.data_atendimento DESC;
"""