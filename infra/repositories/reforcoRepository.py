"""Acesso a dados da tabela tb_reforco_caixa."""

from datetime import datetime
from typing import List

from infra import db
from base.mapTable import mapReforco
from models.reforco import reforco

_COLUNAS = (
    "ID_REFORCO, DATA_REFORCO, DESCRICAO_REFORCO, ID_USUARIO, VALOR_REFORCO, "
    "ID_REFORCO_LOCAL, ID_TERMINAL, ID_ABERTURA"
)


class ReforcoRepository:
    def listar(self, data_minima: datetime, id_abertura: int) -> List[mapReforco]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_reforco_caixa "
            "WHERE DATA_REFORCO >= %s AND ID_ABERTURA = %s"
        )
        return db.query_all(sql, (data_minima, id_abertura), map_cls=mapReforco)

    def inserir(self, dados: reforco, id_usuario: int) -> int:
        sql = (
            "INSERT INTO tb_reforco_caixa "
            "(DATA_REFORCO, DESCRICAO_REFORCO, ID_USUARIO, VALOR_REFORCO, "
            "ID_REFORCO_LOCAL, ID_TERMINAL, ID_ABERTURA) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            datetime.strptime(dados.DATA_REFORCO, "%d/%m/%Y %H:%M"),
            dados.DESCRICAO_REFORCO,
            id_usuario,
            dados.VALOR_REFORCO,
            dados.ID_REFORCO_LOCAL,
            dados.ID_TERMINAL,
            dados.ID_ABERTURA,
        )
        return db.execute(sql, params)

    def listar_por_abertura(self, id_abertura: int) -> List[mapReforco]:
        sql = f"SELECT {_COLUNAS} FROM tb_reforco_caixa WHERE ID_ABERTURA = %s"
        return db.query_all(sql, (id_abertura,), map_cls=mapReforco)

    def soma_por_abertura(self, id_abertura: int):
        sql = "SELECT SUM(VALOR_REFORCO) AS TOTAL FROM tb_reforco_caixa WHERE ID_ABERTURA = %s"
        row = db.query_one(sql, (id_abertura,))
        return row["TOTAL"] if row else None
