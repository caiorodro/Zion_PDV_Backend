"""Acesso a dados da tabela tb_municipio."""

from typing import List, Optional

from infra import db
from base.mapTable import mapMunicipio

_COLUNAS = "ID_IBGE, ID_UF, ID_MUNICIPIO, NOME_MUNICIPIO, SIGLA_UF"


class MunicipioRepository:
    def buscar_por_uf_e_nome(self, uf: str, nome_municipio: str) -> List[mapMunicipio]:
        sql = f"SELECT {_COLUNAS} FROM tb_municipio WHERE SIGLA_UF = %s AND NOME_MUNICIPIO = %s"
        return db.query_all(sql, (uf, nome_municipio), map_cls=mapMunicipio)

    def buscar_primeiro_por_uf_e_nome(self, uf: str, nome_municipio: str) -> Optional[mapMunicipio]:
        sql = f"SELECT {_COLUNAS} FROM tb_municipio WHERE SIGLA_UF = %s AND NOME_MUNICIPIO = %s LIMIT 1"
        return db.query_one(sql, (uf, nome_municipio), map_cls=mapMunicipio)
