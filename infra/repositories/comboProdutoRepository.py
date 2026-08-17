"""Acesso a dados da tabela tb_combo_produto."""

from typing import List

from infra import db
from base.mapTable import mapComboProduto

_COLUNAS = "ID_PRODUTO, ID_PRODUTO_COMBO, QTDE_COMBO, PRECO_COMBO"


class ComboProdutoRepository:
    def listar_por_produto(self, id_produto: int, conn=None) -> List[mapComboProduto]:
        sql = f"SELECT {_COLUNAS} FROM tb_combo_produto WHERE ID_PRODUTO = %s"
        if conn is not None:
            return db.query_all_in(conn, sql, (id_produto,), map_cls=mapComboProduto)
        return db.query_all(sql, (id_produto,), map_cls=mapComboProduto)
