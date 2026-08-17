"""Acesso a dados da tabela tb_empresa."""

from typing import List, Optional

from infra import db
from base.mapTable import mapEmpresa

_COLUNAS = (
    "ID_EMPRESA, NOME_FANTASIA, RAZAO_SOCIAL, CNPJ, NUMERO_NFCE, SERIE_NFCE, ENDERECO, TELEFONE, "
    "CLIENT_ID_IFOOD, CLIENT_SECRET_IFOOD, GRANT_TYPE_IFOOD, MERCHANT_ID_IFOOD, MAQUINA_IMPRESSAO, "
    "EMAIL_LOGIN_ZE, SENHA_LOGIN_ZE, VIAS_IMPRESSAO, IE, BAIRRO, CEP, CIDADE, UF, SERIAL_PROTOCOLO, "
    "CODIGO_MUNICIPIO_IBGE, CRT, FATURAR_TAXA_ENTREGA"
)


class EmpresaRepository:
    def buscar_padrao(self, conn=None) -> Optional[mapEmpresa]:
        """Hoje a aplicação opera com uma única empresa por instalação —
        mesma suposição que o código anterior fazia com `.query(e).first()`."""
        sql = f"SELECT {_COLUNAS} FROM tb_empresa LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, map_cls=mapEmpresa)
        return db.query_one(sql, map_cls=mapEmpresa)

    def listar_todas(self) -> List:
        sql = f"SELECT {_COLUNAS} FROM tb_empresa"
        return db.query_all(sql, map_cls=mapEmpresa)

    def buscar_por_id(self, id_empresa: int) -> Optional[mapEmpresa]:
        sql = f"SELECT {_COLUNAS} FROM tb_empresa WHERE ID_EMPRESA = %s"
        return db.query_one(sql, (id_empresa,), map_cls=mapEmpresa)

    def hora_inicial(self) -> Optional[str]:
        sql = "SELECT HORA_INICIAL FROM tb_empresa LIMIT 1"
        row = db.query_one(sql)
        return row["HORA_INICIAL"] if row else None

    def numero_e_serie_nfce(self, conn=None):
        sql = "SELECT ID_EMPRESA, NUMERO_NFCE, SERIE_NFCE FROM tb_empresa LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql)
        return db.query_one(sql)

    def numero_e_serie_nf(self, id_empresa: int):
        """NUMERO_NF/SERIE_NF — contador da Nota Fiscal "cheia" (DANFE),
        separado de NUMERO_NFCE/SERIE_NFCE (NFC-e). Existe na tabela real mas
        não faz parte de mapEmpresa (só usado neste caminho específico)."""
        sql = "SELECT NUMERO_NF, SERIE_NF FROM tb_empresa WHERE ID_EMPRESA = %s"
        return db.query_one(sql, (id_empresa,))
