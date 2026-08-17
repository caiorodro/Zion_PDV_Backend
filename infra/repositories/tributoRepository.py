"""Acesso a dados da tabela tb_tributo."""

from typing import List, Optional

from infra import db
from base.mapTable import mapTributo

_COLUNAS = (
    "ID_TRIBUTO, NCM, UF_DESTINO, CFOP, CST, ALIQ_ICMS, ALIQ_INTERNA_ICMS, "
    "MODO_BASE_CALCULO_ICMS_ST, IVA, CST_IPI, ALIQ_IPI, CST_PIS, ALIQ_PIS, CST_COFINS, "
    "ALIQ_COFINS, NOME_OPERACAO, CEST, PERCENTUAL_RED_BASE_ICMS, CODIGO_GENERO, ID_EMPRESA, "
    "PERCENTUAL_FCP, IBS, CBS, ISERV"
)


class TributoRepository:
    def buscar_por_id(self, id_tributo: int) -> Optional[mapTributo]:
        sql = f"SELECT {_COLUNAS} FROM tb_tributo WHERE ID_TRIBUTO = %s"
        return db.query_one(sql, (id_tributo,), map_cls=mapTributo)

    def listar(self) -> List[mapTributo]:
        sql = f"SELECT {_COLUNAS} FROM tb_tributo"
        return db.query_all(sql, map_cls=mapTributo)

    def listar_por_ids(self, ids: List[int]) -> List[mapTributo]:
        if not ids:
            return []
        placeholders = ", ".join(["%s"] * len(ids))
        sql = f"SELECT {_COLUNAS} FROM tb_tributo WHERE ID_TRIBUTO IN ({placeholders})"
        return db.query_all(sql, tuple(ids), map_cls=mapTributo)
