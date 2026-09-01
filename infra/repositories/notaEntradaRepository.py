"""Acesso a dados da tabela tb_nota_entrada."""

from datetime import datetime
from types import SimpleNamespace
from typing import List, Optional

from infra import db


class NotaEntradaRepository:
    def listar_distinct(self, data_minima: datetime, nome_like: str) -> List[SimpleNamespace]:
        """Uma linha por nota de fornecedor (NUMERO_NF + CNPJ_FORNECEDOR),
        não por item -- tb_nota_entrada grava um registro por item da nota,
        todos repetindo NUMERO_NF/CNPJ_FORNECEDOR/DATA_EMISSAO, com o XML
        completo (XML_NOTA) só no primeiro registro de cada nota (os demais
        ficam com XML_NOTA vazio). MIN(ID_NF) por grupo é sempre essa linha
        com o XML -- é o ID_NF que buscar_xml() espera. Só entram notas com
        XML de verdade (sem isso não tem base pra montar uma devolução)."""
        # NOME_EMITENTE (coluna, extraída de <xNome> na importação) cobre a
        # razão social; nome fantasia (<xFant>) não tem coluna própria --
        # em vez de depender de tb_fornecedor (cadastro à parte, hoje vazio
        # nesse banco -- confirmado ao vivo), busca direto no texto do
        # próprio XML_NOTA, que sempre tem os dois campos (validado contra
        # nota real: <xNome>Ambev S.A. - CDD Diadema</xNome> e <xFant>CDD
        # DIADEMA</xFant>). NOME_EMITENTE LIKE fica como atalho (evita
        # escanear o XML inteiro quando o nome já bate na coluna curta);
        # XML_NOTA LIKE é quem realmente cobre a busca por nome fantasia.
        like = f"%{nome_like}%"

        sql = (
            "SELECT MIN(ID_NF) AS ID_NF, NUMERO_NF, CNPJ_FORNECEDOR, NOME_EMITENTE, DATA_EMISSAO "
            "FROM tb_nota_entrada "
            "WHERE XML_NOTA IS NOT NULL AND XML_NOTA != '' "
            "AND DATA_EMISSAO >= %s "
            "AND (NOME_EMITENTE LIKE %s OR XML_NOTA LIKE %s) "
            "GROUP BY NUMERO_NF, CNPJ_FORNECEDOR, NOME_EMITENTE, DATA_EMISSAO "
            "ORDER BY DATA_EMISSAO DESC"
        )
        return db.query_all(sql, (data_minima, like, like), map_cls=SimpleNamespace)

    def buscar_xml(self, id_nf: int) -> Optional[str]:
        sql = "SELECT XML_NOTA FROM tb_nota_entrada WHERE ID_NF = %s"
        row = db.query_one(sql, (id_nf,))
        return row["XML_NOTA"] if row else None

    def buscar_itens(self, numero_nf: int, cnpj_fornecedor: str) -> List[SimpleNamespace]:
        """Todas as linhas (uma por item) da mesma nota, na ordem de
        inserção (ID_NF) -- é essa ordem que corresponde a nItem no XML
        (mesmo padrão de importação, confirmado nos dados reais: 4 itens
        na tabela, 4 <det> no XML, mesma ordem). Cada linha traz o
        ID_PRODUTO já vinculado ao cadastro próprio da loja -- é o que
        permite montar a devolução com a tributação (CSOSN/PIS/COFINS) que
        a loja já usa pra esse produto, em vez de tentar traduzir o CST do
        fornecedor (regime fiscal diferente do dela)."""
        sql = (
            "SELECT ID_NF, ID_PRODUTO, DESCRICAO_PRODUTO, PRECO_UNITARIO, QTDE_ITEM "
            "FROM tb_nota_entrada WHERE NUMERO_NF = %s AND CNPJ_FORNECEDOR = %s "
            "ORDER BY ID_NF"
        )
        return db.query_all(sql, (numero_nf, cnpj_fornecedor), map_cls=SimpleNamespace)
