"""Acesso a dados da tabela tb_fechamento_caixa."""

from datetime import datetime
from typing import List

from infra import db
from base.mapTable import mapFechamentoCaixa

_COLUNAS = (
    "ID_FECHAMENTO, ID_ABERTURA, FORMA_PAGTO, VALOR_FECHAMENTO, DATA_FECHAMENTO, "
    "DIFERENCA, ID_FECHAMENTO_LOCAL, ID_TERMINAL"
)


class FechamentoCaixaRepository:
    def listar_por_abertura(self, id_abertura: int) -> List[mapFechamentoCaixa]:
        sql = f"SELECT {_COLUNAS} FROM tb_fechamento_caixa WHERE ID_ABERTURA = %s"
        return db.query_all(sql, (id_abertura,), map_cls=mapFechamentoCaixa)

    def listar(self, id_abertura: int, forma_pagto: str) -> List[mapFechamentoCaixa]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_fechamento_caixa "
            "WHERE ID_ABERTURA = %s AND FORMA_PAGTO = %s"
        )
        return db.query_all(sql, (id_abertura, forma_pagto), map_cls=mapFechamentoCaixa)

    def gravar_fechamento_e_atualizar_abertura(
        self,
        id_abertura: int,
        forma_pagto: str,
        valor_fechamento: float,
        data_fechamento: datetime,
        diferenca: float,
    ) -> int:
        """INSERT em tb_fechamento_caixa + UPDATE em tb_abertura_caixa, atômico
        (o código anterior fazia os dois na mesma sessão SQLAlchemy, com um
        commit só no final)."""
        with db.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO tb_fechamento_caixa "
                    "(ID_ABERTURA, FORMA_PAGTO, VALOR_FECHAMENTO, DATA_FECHAMENTO, DIFERENCA, "
                    "ID_FECHAMENTO_LOCAL, ID_TERMINAL) VALUES (%s, %s, %s, %s, %s, 0, 0)",
                    (id_abertura, forma_pagto, valor_fechamento, data_fechamento, diferenca),
                )
                id_fechamento = cursor.lastrowid

                cursor.execute(
                    "UPDATE tb_abertura_caixa SET VALOR_FECHAMENTO = %s, DATA_FECHAMENTO = %s "
                    "WHERE ID_ABERTURA = %s",
                    (valor_fechamento, data_fechamento, id_abertura),
                )
            finally:
                cursor.close()

        return id_fechamento
