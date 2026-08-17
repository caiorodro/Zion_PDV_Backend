"""Acesso a dados da tabela tb_dose_produto."""

from typing import List

from infra import db
from base.mapTable import mapDoseProduto

_COLUNAS = "ID_PRODUTO_DOSE, ID_PRODUTO, DOSE_ML"


class DoseProdutoRepository:
    def listar_por_produto_dose(self, id_produto_dose: int, conn=None) -> List[mapDoseProduto]:
        """Filtra por ID_PRODUTO_DOSE (não por ID_PRODUTO) — mesmo filtro que
        o código anterior usava em baixaEstoque."""
        sql = f"SELECT {_COLUNAS} FROM tb_dose_produto WHERE ID_PRODUTO_DOSE = %s"
        if conn is not None:
            return db.query_all_in(conn, sql, (id_produto_dose,), map_cls=mapDoseProduto)
        return db.query_all(sql, (id_produto_dose,), map_cls=mapDoseProduto)
