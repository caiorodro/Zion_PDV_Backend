"""Acesso a dados da tabela tb_associacao_produto."""

from typing import List

from infra import db
from base.mapTable import mapAssociacaoProduto

_COLUNAS = "ID_ASSOCIACAO, ID_PRODUTO_ESTOQUE, ID_PRODUTO"


class AssociacaoProdutoRepository:
    def listar_por_produto(self, id_produto: int, conn=None) -> List[mapAssociacaoProduto]:
        sql = f"SELECT {_COLUNAS} FROM tb_associacao_produto WHERE ID_PRODUTO = %s"
        if conn is not None:
            return db.query_all_in(conn, sql, (id_produto,), map_cls=mapAssociacaoProduto)
        return db.query_all(sql, (id_produto,), map_cls=mapAssociacaoProduto)
