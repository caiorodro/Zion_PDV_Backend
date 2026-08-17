"""Acesso a dados da tabela tb_fila_comanda."""

from typing import List

from infra import db
from base.mapTable import mapFilaComanda

_COLUNAS = "ID_FILA, NUMERO_COMANDA, PROCESSADO"


class FilaComandaRepository:
    def inserir(self, numero_comanda: int, processado: int, conn=None) -> int:
        sql = "INSERT INTO tb_fila_comanda (NUMERO_COMANDA, PROCESSADO) VALUES (%s, %s)"
        params = (numero_comanda, processado)
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def listar_por_maquina(self, maquina: int) -> List[mapFilaComanda]:
        sql = f"SELECT {_COLUNAS} FROM tb_fila_comanda WHERE PROCESSADO = %s"
        return db.query_all(sql, (maquina,), map_cls=mapFilaComanda)

    def listar_numeros_distintos_por_maquina(self, maquina: int) -> List[int]:
        sql = "SELECT DISTINCT NUMERO_COMANDA FROM tb_fila_comanda WHERE PROCESSADO = %s"
        return [row["NUMERO_COMANDA"] for row in db.query_all(sql, (maquina,))]

    def deletar_por_comanda(self, numero_comanda: int, conn=None) -> None:
        sql = "DELETE FROM tb_fila_comanda WHERE NUMERO_COMANDA = %s"
        if conn is not None:
            db.execute_in(conn, sql, (numero_comanda,))
        else:
            db.execute(sql, (numero_comanda,))
