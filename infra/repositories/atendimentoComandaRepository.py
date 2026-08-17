"""Acesso a dados da tabela tb_atendimento_comanda."""

from datetime import datetime
from typing import List

from infra import db
from base.mapTable import mapAtendimentoComanda

_COLUNAS = (
    "ID_ATENDIMENTO, NUMERO_COMANDA_ATENDIMENTO, ID_PRODUTO, QTDE, PRECO, NUMERO_COMANDA, FECHADO, "
    "DATA_HORA, ID_TRIBUTO, MESA, OBS_ITEM, IMPRESSAO, AGRUPADOR, IMPRESSAO_PRECONTA, DESCONTO, "
    "ADICIONAL, DESCRICAO_PRODUTO, QTDE_IMPRESSAO, ID_ATENDIMENTO_LOCAL, ID_TERMINAL, NOME_MESA"
)


class AtendimentoComandaRepository:
    def listar_por_comanda(self, numero_comanda: int) -> List[mapAtendimentoComanda]:
        sql = f"SELECT {_COLUNAS} FROM tb_atendimento_comanda WHERE NUMERO_COMANDA = %s"
        return db.query_all(sql, (numero_comanda,), map_cls=mapAtendimentoComanda)

    def inserir(
        self,
        id_produto: int,
        qtde: float,
        preco: float,
        numero_comanda: int,
        id_tributo: int,
        descricao_produto: str,
        conn=None,
    ) -> int:
        sql = (
            "INSERT INTO tb_atendimento_comanda "
            "(NUMERO_COMANDA_ATENDIMENTO, ID_PRODUTO, QTDE, PRECO, NUMERO_COMANDA, FECHADO, "
            "DATA_HORA, ID_TRIBUTO, MESA, OBS_ITEM, IMPRESSAO, AGRUPADOR, IMPRESSAO_PRECONTA, "
            "DESCONTO, ADICIONAL, DESCRICAO_PRODUTO, QTDE_IMPRESSAO, ID_ATENDIMENTO_LOCAL, "
            "ID_TERMINAL, NOME_MESA) "
            "VALUES (0, %s, %s, %s, %s, 1, %s, %s, '', '', 0, 0, 0, 0, 0, %s, 0, 0, 0, '')"
        )
        params = (
            id_produto,
            qtde,
            preco,
            numero_comanda,
            datetime.today(),
            id_tributo,
            descricao_produto,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)
