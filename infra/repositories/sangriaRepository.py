"""Acesso a dados da tabela tb_sangria."""

from datetime import datetime
from typing import List

from infra import db
from base.mapTable import mapSangria
from models.sangria import sangria

_COLUNAS = (
    "ID_SANGRIA, DATA_SANGRIA, DESCRICAO_SANGRIA, ID_USUARIO, VALOR_SANGRIA, "
    "ID_SANGRIA_LOCAL, ID_TERMINAL, ID_ABERTURA"
)


class SangriaRepository:
    def listar(self, data_minima: datetime, id_abertura: int) -> List[mapSangria]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_sangria "
            "WHERE DATA_SANGRIA >= %s AND ID_ABERTURA = %s"
        )
        return db.query_all(sql, (data_minima, id_abertura), map_cls=mapSangria)

    def inserir(self, dados: sangria, id_usuario: int) -> int:
        sql = (
            "INSERT INTO tb_sangria "
            "(DATA_SANGRIA, DESCRICAO_SANGRIA, ID_USUARIO, VALOR_SANGRIA, "
            "ID_SANGRIA_LOCAL, ID_TERMINAL, ID_ABERTURA) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            datetime.strptime(dados.DATA_SANGRIA, "%d/%m/%Y %H:%M"),
            dados.DESCRICAO_SANGRIA,
            id_usuario,
            dados.VALOR_SANGRIA,
            dados.ID_SANGRIA_LOCAL,
            dados.ID_TERMINAL,
            dados.ID_ABERTURA,
        )
        return db.execute(sql, params)

    def listar_por_abertura(self, id_abertura: int) -> List[mapSangria]:
        sql = f"SELECT {_COLUNAS} FROM tb_sangria WHERE ID_ABERTURA = %s"
        return db.query_all(sql, (id_abertura,), map_cls=mapSangria)

    def soma_por_abertura(self, id_abertura: int):
        sql = "SELECT SUM(VALOR_SANGRIA) AS TOTAL FROM tb_sangria WHERE ID_ABERTURA = %s"
        row = db.query_one(sql, (id_abertura,))
        return row["TOTAL"] if row else None

    def listar_para_impressao(self, id_caixa: int) -> List[dict]:
        sql = (
            "SELECT s.DATA_SANGRIA, s.VALOR_SANGRIA, s.DESCRICAO_SANGRIA, "
            "u.NOME_USUARIO, a.DATA_ABERTURA "
            "FROM tb_sangria s "
            "INNER JOIN tb_usuario u ON s.ID_USUARIO = u.ID_USUARIO "
            "INNER JOIN tb_abertura_caixa a ON s.ID_ABERTURA = a.ID_ABERTURA "
            "WHERE s.ID_ABERTURA = %s"
        )
        return db.query_all(sql, (id_caixa,))
