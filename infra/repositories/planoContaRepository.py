"""Acesso a dados da tabela tb_plano_conta."""

from infra import db


class PlanoContaRepository:
    def existe(self, id_plano: str, conn=None) -> bool:
        sql = "SELECT ID_PLANO FROM tb_plano_conta WHERE ID_PLANO = %s LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, (id_plano,)) is not None
        return db.query_one(sql, (id_plano,)) is not None

    def inserir(self, id_plano: str, descricao_plano: str, pai_plano: str, credito_debito: int, conn=None) -> None:
        sql = (
            "INSERT INTO tb_plano_conta (ID_PLANO, DESCRICAO_PLANO, PAI_PLANO, CREDITO_DEBITO) "
            "VALUES (%s, %s, %s, %s)"
        )
        params = (id_plano, descricao_plano, pai_plano, credito_debito)
        if conn is not None:
            db.execute_in(conn, sql, params)
        else:
            db.execute(sql, params)
