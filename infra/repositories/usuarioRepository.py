"""Acesso a dados da tabela tb_usuario."""

from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.mapTable import mapUSUARIO


class UsuarioRepository:
    def buscar_por_id(self, id_usuario: int) -> Optional[mapUSUARIO]:
        sql = (
            "SELECT ID_USUARIO, NOME_USUARIO, SENHA_USUARIO, EMAIL_USUARIO, "
            "USUARIO_ATIVO, TIPO_USUARIO, USUARIO_CAIXA, ACESSO_FECHAMENTO "
            "FROM tb_usuario WHERE ID_USUARIO = %s"
        )
        return db.query_one(sql, (id_usuario,), map_cls=mapUSUARIO)

    def nome_por_id(self, id_usuario: int) -> str:
        """Mesmo comportamento do código anterior: levanta AttributeError se o
        usuário não existir (não engole o erro)."""
        return self.buscar_por_id(id_usuario).NOME_USUARIO

    def nome_e_usuario_caixa(self, id_usuario: int) -> SimpleNamespace:
        sql = "SELECT NOME_USUARIO, USUARIO_CAIXA FROM tb_usuario WHERE ID_USUARIO = %s"
        return db.query_one(sql, (id_usuario,), map_cls=SimpleNamespace)

    def listar_ativos(self) -> List[mapUSUARIO]:
        sql = (
            "SELECT ID_USUARIO, NOME_USUARIO, SENHA_USUARIO, EMAIL_USUARIO, "
            "USUARIO_ATIVO, TIPO_USUARIO, USUARIO_CAIXA, ACESSO_FECHAMENTO "
            "FROM tb_usuario WHERE USUARIO_ATIVO = 1 ORDER BY NOME_USUARIO"
        )
        return db.query_all(sql, map_cls=mapUSUARIO)

    def listar_senhas_admin(self) -> List[str]:
        sql = "SELECT SENHA_USUARIO FROM tb_usuario WHERE TIPO_USUARIO = 1"
        return [row["SENHA_USUARIO"] for row in db.query_all(sql)]

    def existe_admin_com_senha(self, senha: str) -> bool:
        sql = "SELECT ID_USUARIO FROM tb_usuario WHERE SENHA_USUARIO = %s AND TIPO_USUARIO = 1"
        return db.query_one(sql, (senha,)) is not None
