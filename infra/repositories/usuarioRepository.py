"""Acesso a dados da tabela tb_usuario."""

from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.authentication import authentication
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
        # Não dá pra comparar hash Werkzeug direto no SQL (o hash embute um
        # salt aleatório -- o mesmo texto puro nunca gera o mesmo hash duas
        # vezes, então "WHERE SENHA_USUARIO = %s" nunca bateria). Busca as
        # senhas de todos os admins e confere uma a uma em Python, aceitando
        # tanto hash quanto texto puro legado (authentication.verificar_senha).
        return any(
            authentication.verificar_senha(senha, armazenada)
            for armazenada in self.listar_senhas_admin()
        )
