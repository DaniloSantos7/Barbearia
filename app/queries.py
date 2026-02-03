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

# ===============================
# RESUMO SEMANAL
# ===============================
QUERY_RESUMO_SEMANAL = """
SELECT
    COUNT(DISTINCT a.id_atendimento) AS total_atendimentos,
    COALESCE(SUM(v.total), 0) AS faturamento_total
FROM atendimento a
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE a.data_atendimento >= date_trunc('week', CURRENT_DATE)
  AND a.data_atendimento < date_trunc('week', CURRENT_DATE) + interval '7 days';
"""

# ===============================
# FATURAMENTO POR DIA
# ===============================
QUERY_FATURAMENTO_DIA = """
SELECT
    DATE(a.data_atendimento) AS dia,
    COUNT(a.id_atendimento) AS atendimentos,
    SUM(v.total) AS faturamento
FROM atendimento a
LEFT JOIN venda v ON v.id_venda = a.id_venda
WHERE a.data_atendimento >= date_trunc('week', CURRENT_DATE)
  AND a.data_atendimento < date_trunc('week', CURRENT_DATE) + interval '7 days'
GROUP BY dia
ORDER BY dia;
"""

# ===============================
# SERVIÇOS MAIS VENDIDOS
# ===============================
QUERY_SERVICOS_SEMANA = """
SELECT
    s.nome_servico,
    COUNT(iv.id_servico) AS quantidade,
    SUM(iv.valor_unitario) AS faturamento
FROM item_venda iv
JOIN servico s ON s.id_servico = iv.id_servico
JOIN venda v ON v.id_venda = iv.id_venda
WHERE v.id_venda IN (
    SELECT a.id_venda
    FROM atendimento a
    WHERE a.data_atendimento >= date_trunc('week', CURRENT_DATE)
      AND a.data_atendimento < date_trunc('week', CURRENT_DATE) + interval '7 days'
)
GROUP BY s.nome_servico
ORDER BY faturamento DESC;
"""