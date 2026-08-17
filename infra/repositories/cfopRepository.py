"""Acesso a dados da tabela tb_cfop."""

from typing import List

from infra import db
from base.mapTable import mapCFOP

_COLUNAS = "CFOP, DESCRICAO_CFOP, VENDA, DEVOLUCAO"


class CFOPRepository:
    def buscar_por_codigo(self, cfop: str) -> List[mapCFOP]:
        sql = f"SELECT {_COLUNAS} FROM tb_cfop WHERE CFOP = %s"
        return db.query_all(sql, (cfop,), map_cls=mapCFOP)
