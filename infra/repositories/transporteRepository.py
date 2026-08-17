"""Acesso a dados da tabela tb_transporte.

Único lugar que sabe SQL de transporte. views/transporte.py chama este
repositório e cuida só da regra de negócio/formatação da resposta.
"""

from typing import List, Optional

from infra import db
from base.mapTable import mapTransporte
from models.dadosTransporte import dadosTransporte

_COLUNAS = "ID_TRANSPORTE, NOME_TRANSPORTE, CNPJ, IE, ENDERECO, CIDADE, UF, PLACA, EMAIL"


class TransporteRepository:
    def buscar_por_nome(self, filtro_nome: str, limite: int = 150) -> List[mapTransporte]:
        sql = f"SELECT {_COLUNAS} FROM tb_transporte WHERE NOME_TRANSPORTE LIKE %s LIMIT %s"
        return db.query_all(sql, (f"%{filtro_nome}%", limite), map_cls=mapTransporte)

    def listar(self, filtro_nome: str = "", limite: int = 200) -> List[mapTransporte]:
        if filtro_nome:
            sql = f"SELECT {_COLUNAS} FROM tb_transporte WHERE NOME_TRANSPORTE LIKE %s LIMIT %s"
            return db.query_all(sql, (f"%{filtro_nome}%", limite), map_cls=mapTransporte)

        sql = f"SELECT {_COLUNAS} FROM tb_transporte LIMIT %s"
        return db.query_all(sql, (limite,), map_cls=mapTransporte)

    def buscar_por_id(self, id_transporte: int) -> Optional[mapTransporte]:
        sql = f"SELECT {_COLUNAS} FROM tb_transporte WHERE ID_TRANSPORTE = %s"
        return db.query_one(sql, (id_transporte,), map_cls=mapTransporte)

    def buscar_primeiro(self, conn=None) -> Optional[mapTransporte]:
        sql = f"SELECT {_COLUNAS} FROM tb_transporte LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, map_cls=mapTransporte)
        return db.query_one(sql, map_cls=mapTransporte)

    def nome_por_id(self, id_transporte: int, conn=None) -> str:
        """Devolve "" se o transporte não existir (não levanta erro) — mesmo
        comportamento do código anterior."""
        sql = "SELECT NOME_TRANSPORTE FROM tb_transporte WHERE ID_TRANSPORTE = %s"
        row = db.query_one_in(conn, sql, (id_transporte,)) if conn is not None else db.query_one(sql, (id_transporte,))
        return row["NOME_TRANSPORTE"] if row else ""

    def inserir(self, dados: dadosTransporte) -> int:
        sql = (
            "INSERT INTO tb_transporte (NOME_TRANSPORTE, CNPJ, IE, ENDERECO, CIDADE, UF, PLACA, EMAIL) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            dados.NOME_TRANSPORTE,
            dados.CNPJ,
            dados.IE,
            dados.ENDERECO,
            dados.CIDADE,
            dados.UF,
            dados.PLACA,
            dados.EMAIL,
        )
        return db.execute(sql, params)

    def atualizar(self, dados: dadosTransporte) -> None:
        sql = (
            "UPDATE tb_transporte SET NOME_TRANSPORTE = %s, CNPJ = %s, IE = %s, "
            "ENDERECO = %s, CIDADE = %s, UF = %s, PLACA = %s, EMAIL = %s "
            "WHERE ID_TRANSPORTE = %s"
        )
        params = (
            dados.NOME_TRANSPORTE,
            dados.CNPJ,
            dados.IE,
            dados.ENDERECO,
            dados.CIDADE,
            dados.UF,
            dados.PLACA,
            dados.EMAIL,
            dados.ID_TRANSPORTE,
        )
        db.execute(sql, params)
