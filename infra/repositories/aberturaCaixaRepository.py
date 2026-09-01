"""Acesso a dados da tabela tb_abertura_caixa."""

from datetime import datetime
from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.mapTable import mapAberturaCaixa

_COLUNAS = (
    "ID_ABERTURA, ID_EMPRESA, DATA_ABERTURA, VALOR_ABERTURA, "
    "VALOR_FECHAMENTO, ID_USUARIO, DATA_FECHAMENTO, IMPRESSAO"
)


class AberturaCaixaRepository:
    def buscar_por_id(self, id_abertura: int) -> Optional[mapAberturaCaixa]:
        sql = f"SELECT {_COLUNAS} FROM tb_abertura_caixa WHERE ID_ABERTURA = %s"
        return db.query_one(sql, (id_abertura,), map_cls=mapAberturaCaixa)

    def buscar_por_impressao(self, maquina: int) -> Optional[mapAberturaCaixa]:
        sql = f"SELECT {_COLUNAS} FROM tb_abertura_caixa WHERE IMPRESSAO = %s LIMIT 1"
        return db.query_one(sql, (maquina,), map_cls=mapAberturaCaixa)

    def usuario_da_abertura(self, id_abertura: int) -> int:
        """Mesmo comportamento do código anterior: levanta IndexError se a
        abertura não existir (não engole o erro)."""
        sql = "SELECT ID_USUARIO FROM tb_abertura_caixa WHERE ID_ABERTURA = %s"
        rows = db.query_all(sql, (id_abertura,))
        return rows[0]["ID_USUARIO"]

    def buscar_aberta_recente(self, id_usuario: int, data_limite: datetime) -> Optional[dict]:
        """Usado por gravaAberturaCaixa() pra bloquear abrir um segundo caixa
        se o usuário já tiver um aberto nas últimas 24h. Mesmo critério de
        "aberto" de listar_abertos_com_usuario: sem registro em
        tb_fechamento_caixa, além do VALOR_FECHAMENTO = 0."""
        sql = (
            "SELECT ID_ABERTURA FROM tb_abertura_caixa a "
            "WHERE a.ID_USUARIO = %s AND a.DATA_ABERTURA >= %s AND a.VALOR_FECHAMENTO = 0 "
            "AND NOT EXISTS ("
            "SELECT 1 FROM tb_fechamento_caixa f WHERE f.ID_ABERTURA = a.ID_ABERTURA"
            ") "
            "LIMIT 1"
        )
        return db.query_one(sql, (id_usuario, data_limite))

    def inserir(self, data_abertura: datetime, valor_abertura: float, id_usuario: int) -> int:
        sql = (
            "INSERT INTO tb_abertura_caixa (DATA_ABERTURA, VALOR_ABERTURA, VALOR_FECHAMENTO, "
            "ID_USUARIO, DATA_FECHAMENTO) VALUES (%s, %s, 0, %s, NULL)"
        )
        return db.execute(sql, (data_abertura, valor_abertura, id_usuario))

    def atualizar_impressao(self, id_abertura: int, valor: int) -> None:
        sql = "UPDATE tb_abertura_caixa SET IMPRESSAO = %s WHERE ID_ABERTURA = %s"
        db.execute(sql, (valor, id_abertura))

    def atualizar_fechamento(self, id_abertura: int, valor_fechamento: float, data_fechamento: datetime) -> None:
        sql = (
            "UPDATE tb_abertura_caixa SET VALOR_FECHAMENTO = %s, DATA_FECHAMENTO = %s "
            "WHERE ID_ABERTURA = %s"
        )
        db.execute(sql, (valor_fechamento, data_fechamento, id_abertura))

    def listar_abertos_com_usuario(self, data_minima: datetime) -> List[SimpleNamespace]:
        """Usado por listCaixa(): caixas abertos desde `data_minima`, com
        dados do usuário. Considera fechado (e por isso exclui) qualquer
        abertura que já tenha registro em tb_fechamento_caixa — critério mais
        confiável do que só `VALOR_FECHAMENTO = 0`, mantido também como
        checagem extra."""
        sql = (
            "SELECT a.ID_ABERTURA, a.DATA_ABERTURA, a.VALOR_ABERTURA, a.VALOR_FECHAMENTO, "
            "u.NOME_USUARIO, u.TIPO_USUARIO, u.USUARIO_CAIXA "
            "FROM tb_abertura_caixa a "
            "INNER JOIN tb_usuario u ON a.ID_USUARIO = u.ID_USUARIO "
            "WHERE a.DATA_ABERTURA >= %s AND a.VALOR_FECHAMENTO = 0 "
            "AND NOT EXISTS ("
            "SELECT 1 FROM tb_fechamento_caixa f WHERE f.ID_ABERTURA = a.ID_ABERTURA"
            ") "
            "ORDER BY a.DATA_ABERTURA"
        )
        return db.query_all(sql, (data_minima,), map_cls=SimpleNamespace)

    def listar_recentes_com_usuario(self, data_minima: datetime) -> List[SimpleNamespace]:
        """Usado por listaUltimosCaixas(): todos os caixas (abertos ou não)
        desde `data_minima`, com o nome do usuário."""
        sql = (
            "SELECT a.ID_ABERTURA, a.DATA_ABERTURA, a.VALOR_ABERTURA, a.VALOR_FECHAMENTO, "
            "u.NOME_USUARIO, a.DATA_FECHAMENTO "
            "FROM tb_abertura_caixa a "
            "INNER JOIN tb_usuario u ON a.ID_USUARIO = u.ID_USUARIO "
            "WHERE a.DATA_ABERTURA >= %s"
        )
        return db.query_all(sql, (data_minima,), map_cls=SimpleNamespace)

    def listar_historico_com_usuario(self, data_minima: datetime) -> List[SimpleNamespace]:
        """Usado por listaCaixasAnteriores(): histórico desde `data_minima`."""
        sql = (
            "SELECT a.ID_ABERTURA, a.DATA_ABERTURA, u.NOME_USUARIO "
            "FROM tb_abertura_caixa a "
            "INNER JOIN tb_usuario u ON a.ID_USUARIO = u.ID_USUARIO "
            "WHERE a.DATA_ABERTURA > %s"
        )
        return db.query_all(sql, (data_minima,), map_cls=SimpleNamespace)
