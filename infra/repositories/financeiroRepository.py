"""Acesso a dados da tabela tb_financeiro."""

from datetime import datetime
from typing import Optional

from infra import db


class FinanceiroRepository:
    def deletar_por_comanda(self, numero_comanda: int, conn=None) -> None:
        sql = "DELETE FROM tb_financeiro WHERE NUMERO_COMANDA = %s"
        if conn is not None:
            db.execute_in(conn, sql, (numero_comanda,))
        else:
            db.execute(sql, (numero_comanda,))

    def buscar_por_comanda(self, numero_comanda: int) -> Optional[dict]:
        sql = "SELECT ID_FINANCEIRO, NUMERO_COMANDA FROM tb_financeiro WHERE NUMERO_COMANDA = %s LIMIT 1"
        return db.query_one(sql, (numero_comanda,))

    def atualizar_historico(self, numero_comanda: int, historico: str) -> None:
        sql = "UPDATE tb_financeiro SET HISTORICO = %s WHERE NUMERO_COMANDA = %s"
        db.execute(sql, (historico, numero_comanda))

    def inserir(
        self,
        data_vencimento: datetime,
        historico: str,
        id_plano: str,
        valor: float,
        valor_desconto: float,
        valor_total: float,
        numero_comanda: int,
        conn=None,
    ) -> int:
        sql = (
            "INSERT INTO tb_financeiro "
            "(DATA_LANCAMENTO, DATA_VENCIMENTO, DATA_PAGAMENTO, HISTORICO, ID_PLANO, VALOR, "
            "VALOR_DESCONTO, VALOR_ACRESCIMO, VALOR_TOTAL, CREDITO_DEBITO, NUMERO_SEQ_NF_ENTRADA, "
            "ID_EMPRESA, NUMERO_COMANDA) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, 0, 0, 1, %s)"
        )
        params = (
            datetime.today(),
            data_vencimento,
            datetime(1901, 1, 1),
            historico,
            id_plano,
            valor,
            valor_desconto,
            valor_total,
            numero_comanda,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)
