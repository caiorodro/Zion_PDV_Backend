"""Acesso a dados da tabela tb_estoque."""

from datetime import datetime

from infra import db
from models.estoque import estoque


class EstoqueRepository:
    def soma_qtde(self, id_produto: int, movimento: int):
        """SUM(QTDE_ESTOQUE) para um produto e um sentido de movimento
        (0 = entrada, 1 = saída). None se não houver nenhum lançamento."""
        sql = (
            "SELECT SUM(QTDE_ESTOQUE) AS TOTAL FROM tb_estoque "
            "WHERE ID_PRODUTO = %s AND MOVIMENTO = %s"
        )
        row = db.query_one(sql, (id_produto, movimento))
        return row["TOTAL"] if row else None

    def inserir(self, dados: estoque, conn=None) -> int:
        sql = (
            "INSERT INTO tb_estoque (DATA_ESTOQUE, ID_PRODUTO, MOVIMENTO, QTDE_ESTOQUE, "
            "ID_FORNECEDOR, ID_EMPRESA, SALDO, NUMERO_COMANDA, PRECO_CUSTO, CONTAGEM) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            datetime.strptime(dados.DATA_ESTOQUE, "%d/%m/%Y %H:%M"),
            dados.ID_PRODUTO,
            dados.MOVIMENTO,
            dados.QTDE_ESTOQUE,
            dados.ID_FORNECEDOR,
            dados.ID_EMPRESA,
            dados.SALDO,
            dados.NUMERO_COMANDA,
            dados.PRECO_CUSTO,
            dados.CONTAGEM,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def inserir_movimento(
        self,
        id_produto: int,
        movimento: int,
        qtde_estoque: float,
        numero_comanda: int,
        saldo: float,
        conn=None,
    ) -> int:
        """Lançamento de estoque a partir da venda de um item (baixaEstoque) —
        campos fixos (ID_FORNECEDOR=None, ID_EMPRESA=1, PRECO_CUSTO=0, CONTAGEM=0)
        iguais aos que o código anterior usava nesse fluxo."""
        sql = (
            "INSERT INTO tb_estoque (DATA_ESTOQUE, ID_PRODUTO, MOVIMENTO, QTDE_ESTOQUE, "
            "ID_FORNECEDOR, ID_EMPRESA, SALDO, NUMERO_COMANDA, PRECO_CUSTO, CONTAGEM) "
            "VALUES (%s, %s, %s, %s, NULL, 1, %s, %s, 0.00, 0)"
        )
        params = (datetime.today(), id_produto, movimento, qtde_estoque, saldo, numero_comanda)
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)
