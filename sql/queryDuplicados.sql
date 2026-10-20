-- ============================================================
-- 1) BACKUP -- cria tabelas com cópia do que será apagado.
--    Roda de novo no futuro? Só acumula mais linhas de backup, sem problema.
-- ============================================================
CREATE TABLE IF NOT EXISTS backup_duplicados_pedido LIKE tb_pedido;
CREATE TABLE IF NOT EXISTS backup_duplicados_item_pedido LIKE tb_item_pedido;
CREATE TABLE IF NOT EXISTS backup_duplicados_pedido_pagamento LIKE tb_pedido_pagamento;
CREATE TABLE IF NOT EXISTS backup_duplicados_atendimento_comanda LIKE tb_atendimento_comanda;

-- ============================================================
-- 2) Lista de NUMERO_PEDIDO a apagar: todos MENOS o de menor
--    NUMERO_PEDIDO em cada grupo de INTERNAL_KEY_ZION duplicada.
-- ============================================================
DROP TEMPORARY TABLE IF EXISTS tmp_pedidos_duplicados_apagar;

CREATE TEMPORARY TABLE tmp_pedidos_duplicados_apagar AS
SELECT p.NUMERO_PEDIDO
FROM tb_pedido p
JOIN (
    SELECT INTERNAL_KEY_ZION, MIN(NUMERO_PEDIDO) AS MANTER
    FROM tb_pedido
    WHERE INTERNAL_KEY_ZION IS NOT NULL AND INTERNAL_KEY_ZION <> ''
    GROUP BY INTERNAL_KEY_ZION
    HAVING COUNT(*) > 1
) grupos ON grupos.INTERNAL_KEY_ZION = p.INTERNAL_KEY_ZION
WHERE p.NUMERO_PEDIDO <> grupos.MANTER;

-- CONFIRA a lista antes de continuar -- confere com o que você já viu de duplicidade?
SELECT * FROM tmp_pedidos_duplicados_apagar;

-- ============================================================
-- 3) Diagnóstico extra ANTES de apagar: algum desses pedidos mexeu
--    em estoque (produto combo) ou financeiro (forma de pagamento
--    "a prazo"/fiado)? Se aparecer algo aqui, PARE e me avise antes
--    de prosseguir -- reverter isso não é automático nesse script.
-- ============================================================
SELECT * FROM tb_estoque
WHERE NUMERO_COMANDA IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

-- ============================================================
-- 4) Guarda backup das linhas que serão apagadas
-- ============================================================
INSERT INTO backup_duplicados_pedido
SELECT * FROM tb_pedido WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

INSERT INTO backup_duplicados_item_pedido
SELECT * FROM tb_item_pedido WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

INSERT INTO backup_duplicados_pedido_pagamento
SELECT * FROM tb_pedido_pagamento WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

INSERT INTO backup_duplicados_atendimento_comanda
SELECT * FROM tb_atendimento_comanda WHERE NUMERO_COMANDA IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

-- Confira: essa contagem tem que bater com o total de linhas do passo 2
SELECT COUNT(*) AS BACKUP_PEDIDOS FROM backup_duplicados_pedido;

-- ============================================================
-- 5) DELETE de verdade, em transação, na ordem que respeita as FKs.
--    SÓ prossiga se os SELECTs acima conferem com o esperado.
-- ============================================================
START TRANSACTION;

DELETE FROM tb_pedido_pagamento
WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

DELETE FROM tb_item_pedido
WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

DELETE FROM tb_atendimento_comanda
WHERE NUMERO_COMANDA IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

-- Defensivo: você confirmou que não teve emissão fiscal nesses duplicados,
-- mas isso evita erro de FK caso apareça algum registro inesperado.
DELETE FROM tb_pedido_nfe
WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

DELETE FROM tb_pedido
WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

-- Confira ANTES do commit -- deve devolver 0:
SELECT COUNT(*) FROM tb_pedido
WHERE NUMERO_PEDIDO IN (SELECT NUMERO_PEDIDO FROM tmp_pedidos_duplicados_apagar);

-- Se estiver tudo certo:
COMMIT;
-- Se algo parecer errado: ROLLBACK; (em vez de COMMIT)