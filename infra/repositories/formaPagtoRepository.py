"""Acesso a dados da tabela tb_forma_pagto."""

from typing import List, Optional

from infra import db
from base.mapTable import mapFormaPagto

_COLUNAS = (
    "ID_FORMA, DESCRICAO_FORMA, PAGTO_FUTURO, VALE_FUNCIONARIO, VALOR_DIA, "
    "TAXA_PAGAMENTO, DIAS_PAGAMENTO"
)


class FormaPagtoRepository:
    def buscar_por_descricao(self, descricao: str, conn=None) -> Optional[mapFormaPagto]:
        sql = f"SELECT {_COLUNAS} FROM tb_forma_pagto WHERE DESCRICAO_FORMA = %s LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, (descricao,), map_cls=mapFormaPagto)
        return db.query_one(sql, (descricao,), map_cls=mapFormaPagto)

    def listar(self) -> List[mapFormaPagto]:
        sql = f"SELECT {_COLUNAS} FROM tb_forma_pagto ORDER BY DESCRICAO_FORMA"
        return db.query_all(sql, map_cls=mapFormaPagto)

    def existe_pagto_futuro_entre(self, descricoes: List[str]) -> bool:
        if not descricoes:
            return False

        placeholders = ", ".join(["%s"] * len(descricoes))
        sql = (
            f"SELECT ID_FORMA FROM tb_forma_pagto "
            f"WHERE DESCRICAO_FORMA IN ({placeholders}) AND PAGTO_FUTURO = 1 LIMIT 1"
        )
        return db.query_one(sql, tuple(descricoes)) is not None
