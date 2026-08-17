"""Acesso a dados da tabela tb_pedido_pagamento.

Só o que já foi migrado até agora. O grosso é migrado junto com views/pedido.py.
"""

from types import SimpleNamespace
from typing import List, Optional

from datetime import datetime

from infra import db
from base.mapTable import mapPedidoPagamento
from models.pedidoPagamento import pedidoPagamento

_COLUNAS = (
    "ID_PAGAMENTO, NUMERO_PEDIDO, DATA_HORA, FORMA_PAGTO, VALOR_PAGO, ID_CAIXA, ORIGEM, "
    "ID_PAGAMENTO_LOCAL, ID_TERMINAL, CODIGO_NSU, VALOR_PAGO_STONE, DATA_AUTORIZACAO, BANDEIRA"
)


class PedidoPagamentoRepository:
    def listar_por_pedido(self, numero_pedido: int, conn=None) -> List[mapPedidoPagamento]:
        sql = f"SELECT {_COLUNAS} FROM tb_pedido_pagamento WHERE NUMERO_PEDIDO = %s"
        if conn is not None:
            return db.query_all_in(conn, sql, (numero_pedido,), map_cls=mapPedidoPagamento)
        return db.query_all(sql, (numero_pedido,), map_cls=mapPedidoPagamento)

    def forma_pagto_por_pedido(self, numero_pedido: int, conn=None) -> Optional[str]:
        sql = "SELECT FORMA_PAGTO FROM tb_pedido_pagamento WHERE NUMERO_PEDIDO = %s LIMIT 1"
        if conn is not None:
            row = db.query_one_in(conn, sql, (numero_pedido,))
        else:
            row = db.query_one(sql, (numero_pedido,))
        return row["FORMA_PAGTO"] if row else None

    def inserir(self, item: pedidoPagamento, conn=None) -> int:
        forma_pagto = item.FORMA_PAGTO
        if "." in forma_pagto:
            forma_pagto = forma_pagto[forma_pagto.index(".") + 1:].strip()

        sql = (
            "INSERT INTO tb_pedido_pagamento (NUMERO_PEDIDO, DATA_HORA, FORMA_PAGTO, VALOR_PAGO, "
            "ID_CAIXA, ORIGEM, ID_PAGAMENTO_LOCAL, ID_TERMINAL, CODIGO_NSU, VALOR_PAGO_STONE, "
            "DATA_AUTORIZACAO, BANDEIRA) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            item.NUMERO_PEDIDO,
            datetime.strptime(item.DATA_HORA, "%d/%m/%Y %H:%M"),
            forma_pagto,
            item.VALOR_PAGO,
            item.ID_CAIXA,
            item.ORIGEM,
            item.ID_PAGAMENTO_LOCAL,
            item.ID_TERMINAL,
            item.CODIGO_NSU,
            item.VALOR_PAGO_STONE,
            datetime.strptime(item.DATA_AUTORIZACAO, "%d/%m/%Y %H:%M"),
            item.BANDEIRA,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def formas_pagto_do_caixa(self, id_caixa: int) -> List[str]:
        sql = (
            "SELECT DISTINCT pg.FORMA_PAGTO FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s"
        )
        return [row["FORMA_PAGTO"] for row in db.query_all(sql, (id_caixa,))]

    def total_por_forma(self, id_caixa: int, forma_pagto: str) -> Optional[SimpleNamespace]:
        sql = (
            "SELECT pg.FORMA_PAGTO, SUM(pg.VALOR_PAGO) AS TOTAL_PAGO FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s AND pg.FORMA_PAGTO = %s "
            "GROUP BY pg.FORMA_PAGTO"
        )
        return db.query_one(sql, (id_caixa, forma_pagto), map_cls=SimpleNamespace)

    def totais_agrupados_por_forma(self, id_caixa: int) -> List[SimpleNamespace]:
        sql = (
            "SELECT pg.FORMA_PAGTO, SUM(pg.VALOR_PAGO) AS TOTAL_PAGO FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s GROUP BY pg.FORMA_PAGTO"
        )
        return db.query_all(sql, (id_caixa,), map_cls=SimpleNamespace)

    def totais_agrupados_por_origem(self, id_caixa: int) -> List[SimpleNamespace]:
        sql = (
            "SELECT pg.ORIGEM, SUM(pg.VALOR_PAGO) AS TOTAL_PAGO FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s GROUP BY pg.ORIGEM"
        )
        return db.query_all(sql, (id_caixa,), map_cls=SimpleNamespace)

    def totais_agrupados_por_forma_e_origem(self, id_caixa: int) -> List[SimpleNamespace]:
        sql = (
            "SELECT pg.FORMA_PAGTO, pg.ORIGEM, SUM(pg.VALOR_PAGO) AS TOTAL_PAGO "
            "FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s GROUP BY pg.FORMA_PAGTO, pg.ORIGEM"
        )
        return db.query_all(sql, (id_caixa,), map_cls=SimpleNamespace)

    def soma_pagamentos_do_caixa(self, id_caixa: int):
        sql = (
            "SELECT SUM(pg.VALOR_PAGO) AS VALOR_PAGO FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s"
        )
        row = db.query_one(sql, (id_caixa,))
        return row["VALOR_PAGO"] if row else None

    def listar_pagamentos_do_caixa(self, id_caixa: int, forma_pagto: str) -> List[SimpleNamespace]:
        sql = (
            "SELECT p.NUMERO_PEDIDO, p.DATA_HORA, p.STATUS_PEDIDO, p.NOME_CLIENTE, p.TOTAL_PEDIDO, "
            "p.TROCO, pg.VALOR_PAGO, pg.CODIGO_NSU, pg.ID_PAGAMENTO, pg.VALOR_PAGO_STONE, pg.FORMA_PAGTO "
            "FROM tb_pedido_pagamento pg "
            "INNER JOIN tb_pedido p ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE p.ID_CAIXA = %s AND pg.FORMA_PAGTO = %s AND p.STATUS_PEDIDO = 3"
        )
        return db.query_all(sql, (id_caixa, forma_pagto), map_cls=SimpleNamespace)

    def atualizar_nsu(self, id_pagamento: int, nsu: str) -> None:
        sql = "UPDATE tb_pedido_pagamento SET CODIGO_NSU = %s WHERE ID_PAGAMENTO = %s"
        db.execute(sql, (nsu, id_pagamento))

    def atualizar_valor_pago_stone(self, id_pagamento: int, valor: float) -> None:
        sql = "UPDATE tb_pedido_pagamento SET VALOR_PAGO_STONE = %s WHERE ID_PAGAMENTO = %s"
        db.execute(sql, (valor, id_pagamento))

    def atualizar_autorizacao(
        self, numero_pedido: int, valor_pago: float, nsu: str, data_autorizacao, bandeira: str, id_terminal,
    ) -> None:
        """Grava a confirmação de um pagamento com maquininha (Stone) — chega
        depois do pedido já ter sido salvo, por isso é um UPDATE em vez de
        fazer parte do INSERT original do pagamento."""
        sql = (
            "UPDATE tb_pedido_pagamento SET VALOR_PAGO_STONE = %s, CODIGO_NSU = %s, "
            "DATA_AUTORIZACAO = %s, BANDEIRA = %s, ID_TERMINAL = %s WHERE NUMERO_PEDIDO = %s"
        )
        params = (valor_pago, nsu, data_autorizacao, bandeira, id_terminal, numero_pedido)
        db.execute(sql, params)

    def buscar_por_id(self, id_pagamento: int) -> Optional[mapPedidoPagamento]:
        sql = f"SELECT {_COLUNAS} FROM tb_pedido_pagamento WHERE ID_PAGAMENTO = %s"
        return db.query_one(sql, (id_pagamento,), map_cls=mapPedidoPagamento)

    def deletar_por_id(self, id_pagamento: int) -> None:
        sql = "DELETE FROM tb_pedido_pagamento WHERE ID_PAGAMENTO = %s"
        db.execute(sql, (id_pagamento,))

    def inserir_avulso(
        self, numero_pedido: int, data_hora, forma_pagto: str, valor_pago: float,
        id_caixa: int, origem: str,
    ) -> int:
        """Pagamento adicionado manualmente na edição do pedido — sem CODIGO_NSU,
        VALOR_PAGO_STONE, DATA_AUTORIZACAO ou BANDEIRA (mesmos valores em
        branco/zero que o código anterior usava nesse fluxo)."""
        sql = (
            "INSERT INTO tb_pedido_pagamento (NUMERO_PEDIDO, DATA_HORA, FORMA_PAGTO, VALOR_PAGO, "
            "ID_CAIXA, ORIGEM, ID_PAGAMENTO_LOCAL, ID_TERMINAL, CODIGO_NSU, VALOR_PAGO_STONE, "
            "DATA_AUTORIZACAO, BANDEIRA) VALUES (%s, %s, %s, %s, %s, %s, 0, 0, '', 0, NULL, '')"
        )
        params = (numero_pedido, data_hora, forma_pagto, valor_pago, id_caixa, origem)
        return db.execute(sql, params)
