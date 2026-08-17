"""Acesso a dados da tabela tb_grade_produto (preços por faixa de quantidade)."""

from typing import List

from infra import db
from base.mapTable import mapGradePreco

_COLUNAS = "ID_PRODUTO, QTDE_INICIAL, QTDE_FINAL, PRECO_VENDA"


class GradePrecoRepository:
    def buscar_faixa(self, id_produto: int, qtde) -> List[mapGradePreco]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_grade_produto "
            "WHERE ID_PRODUTO = %s AND QTDE_INICIAL <= %s AND QTDE_FINAL > %s"
        )
        return db.query_all(sql, (id_produto, qtde, qtde), map_cls=mapGradePreco)

    def listar_todas(self) -> List[mapGradePreco]:
        sql = f"SELECT {_COLUNAS} FROM tb_grade_produto"
        return db.query_all(sql, map_cls=mapGradePreco)
