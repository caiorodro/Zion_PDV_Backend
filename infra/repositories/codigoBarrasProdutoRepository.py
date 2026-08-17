"""Acesso a dados da tabela tb_codigo_barras_produto."""

from typing import List

from infra import db
from base.mapTable import mapCodigoBarrasProduto

_COLUNAS = "ID_BARRAS, ID_PRODUTO, CODIGO_BARRAS_PRODUTO"


class CodigoBarrasProdutoRepository:
    def listar_por_produto(self, id_produto: int) -> List[mapCodigoBarrasProduto]:
        sql = f"SELECT {_COLUNAS} FROM tb_codigo_barras_produto WHERE ID_PRODUTO = %s"
        return db.query_all(sql, (id_produto,), map_cls=mapCodigoBarrasProduto)
