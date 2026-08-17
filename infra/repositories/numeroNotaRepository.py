"""Acesso a dados da tabela tb_numero_nota (contador de NF-e por série,
usado pelo fluxo de emissão via Zeus — separado do contador de NFC-e que
mora em tb_empresa)."""

from typing import List, Optional

from infra import db
from base.mapTable import mapNUMERO_NOTA

_COLUNAS = "ID_NUMERO, NUMERO_NF, SERIE_NF"


class NumeroNotaRepository:
    def buscar_por_serie(self, serie_nf: str) -> List[mapNUMERO_NOTA]:
        sql = f"SELECT {_COLUNAS} FROM tb_numero_nota WHERE SERIE_NF = %s"
        return db.query_all(sql, (serie_nf,), map_cls=mapNUMERO_NOTA)

    def inserir(self, serie_nf: str) -> int:
        sql = "INSERT INTO tb_numero_nota (NUMERO_NF, SERIE_NF) VALUES (0, %s)"
        return db.execute(sql, (serie_nf,))

    def atualizar_numero(self, serie_nf: str, numero_nf: int, conn=None) -> None:
        sql = "UPDATE tb_numero_nota SET NUMERO_NF = %s WHERE SERIE_NF = %s"
        params = (numero_nf, serie_nf)
        if conn is not None:
            db.execute_in(conn, sql, params)
        else:
            db.execute(sql, params)
