"""Acesso a dados da tabela tb_produto."""

from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.mapTable import mapProduto

_COLUNAS_COMPLETAS = (
    "ID_PRODUTO, CODIGO_PRODUTO, CODIGO_PRODUTO_PDV, DESCRICAO_PRODUTO, PRECO_BALCAO, "
    "PRECO_DELIVERY, PRECO_ATACADO, PRODUTO_ATIVO, ID_TRIBUTO, CODIGO_ZE, ID_FAMILIA, FOTO_PRODUTO"
)


class ProdutoRepository:
    def descricao_por_id(self, id_produto: int) -> str:
        """Mesmo comportamento do código anterior (views/CupomFiscal.py):
        levanta erro se o produto não existir (não engole o erro)."""
        sql = "SELECT DESCRICAO_PRODUTO FROM tb_produto WHERE ID_PRODUTO = %s"
        return db.query_one(sql, (id_produto,))["DESCRICAO_PRODUTO"]

    def listar_descricoes_por_ids(self, ids: List[int]) -> List[SimpleNamespace]:
        if not ids:
            return []
        placeholders = ", ".join(["%s"] * len(ids))
        sql = f"SELECT ID_PRODUTO, DESCRICAO_PRODUTO FROM tb_produto WHERE ID_PRODUTO IN ({placeholders})"
        return db.query_all(sql, tuple(ids), map_cls=SimpleNamespace)

    def codigo_pdv_por_id(self, id_produto: int):
        sql = "SELECT CODIGO_PRODUTO_PDV FROM tb_produto WHERE ID_PRODUTO = %s"
        row = db.query_one(sql, (id_produto,))
        return row["CODIGO_PRODUTO_PDV"] if row else None

    def existe(self, id_produto: int, conn=None) -> bool:
        sql = "SELECT ID_PRODUTO FROM tb_produto WHERE ID_PRODUTO = %s LIMIT 1"
        if conn is not None:
            return db.query_one_in(conn, sql, (id_produto,)) is not None
        return db.query_one(sql, (id_produto,)) is not None

    def descricao_por_id_ou_vazio(self, id_produto: int, conn=None) -> str:
        """Mesmo comportamento do código anterior (views/pedido.py): devolve
        "" se o produto não existir, em vez de levantar erro."""
        sql = "SELECT DESCRICAO_PRODUTO FROM tb_produto WHERE ID_PRODUTO = %s"
        row = db.query_one_in(conn, sql, (id_produto,)) if conn is not None else db.query_one(sql, (id_produto,))
        return row["DESCRICAO_PRODUTO"] if row else ""

    def buscar_codigo_tributo_preco(self, id_produto: int) -> SimpleNamespace:
        """CODIGO_PRODUTO/ID_TRIBUTO/PRECO_BALCAO — usado por pedido.addItem().
        Mesmo comportamento do código anterior: levanta erro se o produto não
        existir (não engole o erro)."""
        sql = "SELECT ID_PRODUTO, CODIGO_PRODUTO, ID_TRIBUTO, PRECO_BALCAO FROM tb_produto WHERE ID_PRODUTO = %s"
        return db.query_one(sql, (id_produto,), map_cls=SimpleNamespace)

    def listar_ativos(self, nome: str = "", limite: Optional[int] = 50) -> List[SimpleNamespace]:
        """Usado por produto.list(): ID_PRODUTO/DESCRICAO_PRODUTO/PRECO_BALCAO/ID_TRIBUTO
        de produtos ativos com preço > 0, ordenado por descrição. Sem `nome`,
        limita a 50 (comportamento original); com `nome`, sem limite."""
        sql = (
            "SELECT ID_PRODUTO, DESCRICAO_PRODUTO, PRECO_BALCAO, ID_TRIBUTO FROM tb_produto "
            "WHERE PRECO_BALCAO > 0.00 AND PRODUTO_ATIVO = 1"
        )
        params: list = []

        if nome:
            sql += " AND DESCRICAO_PRODUTO LIKE %s"
            params.append(f"%{nome}%")

        sql += " ORDER BY DESCRICAO_PRODUTO, PRODUTO_ATIVO"

        if not nome and limite is not None:
            sql += " LIMIT %s"
            params.append(limite)

        return db.query_all(sql, tuple(params), map_cls=SimpleNamespace)

    def buscar_resumo_por_id(self, id_produto: int) -> Optional[SimpleNamespace]:
        """ID_PRODUTO/DESCRICAO_PRODUTO/PRECO_BALCAO/PRODUTO_ATIVO/ID_TRIBUTO."""
        sql = (
            "SELECT ID_PRODUTO, DESCRICAO_PRODUTO, PRECO_BALCAO, PRODUTO_ATIVO, ID_TRIBUTO "
            "FROM tb_produto WHERE ID_PRODUTO = %s"
        )
        return db.query_one(sql, (id_produto,), map_cls=SimpleNamespace)

    def preco_balcao_por_id(self, id_produto: int) -> Optional[SimpleNamespace]:
        sql = "SELECT ID_PRODUTO, PRECO_BALCAO FROM tb_produto WHERE ID_PRODUTO = %s"
        return db.query_one(sql, (id_produto,), map_cls=SimpleNamespace)

    def buscar_por_codigo_produto(self, codigo_produto: str) -> List[mapProduto]:
        """Linha completa (inclusive FOTO_PRODUTO) — usado pela leitura de balança."""
        sql = f"SELECT {_COLUNAS_COMPLETAS} FROM tb_produto WHERE CODIGO_PRODUTO = %s"
        return db.query_all(sql, (codigo_produto,), map_cls=mapProduto)

    def buscar_ativo_por_codigo_pdv(self, codigo: str) -> Optional[SimpleNamespace]:
        sql = (
            "SELECT ID_PRODUTO, DESCRICAO_PRODUTO, PRECO_BALCAO, ID_TRIBUTO, ID_FAMILIA "
            "FROM tb_produto WHERE CODIGO_PRODUTO_PDV = %s AND PRECO_BALCAO > 0.00 AND PRODUTO_ATIVO = 1"
        )
        return db.query_one(sql, (codigo,), map_cls=SimpleNamespace)

    def buscar_ativo_por_codigo(self, codigo: str) -> Optional[SimpleNamespace]:
        sql = (
            "SELECT ID_PRODUTO, DESCRICAO_PRODUTO, PRECO_BALCAO, ID_TRIBUTO, ID_FAMILIA "
            "FROM tb_produto WHERE CODIGO_PRODUTO = %s AND PRECO_BALCAO > 0.00 AND PRODUTO_ATIVO = 1"
        )
        return db.query_one(sql, (codigo,), map_cls=SimpleNamespace)

    def buscar_similares(self, termos: List[str], limite: int = 50) -> List[mapProduto]:
        """Linha completa, com um LIKE por termo de busca (todos precisam bater)."""
        sql = f"SELECT {_COLUNAS_COMPLETAS} FROM tb_produto"
        params: list = []

        if termos:
            condicoes = " AND ".join(["DESCRICAO_PRODUTO LIKE %s"] * len(termos))
            sql += f" WHERE {condicoes}"
            params.extend(f"%{termo}%" for termo in termos)

        sql += " LIMIT %s"
        params.append(limite)

        return db.query_all(sql, tuple(params), map_cls=mapProduto)

    def listar_ativos_completo(self) -> List[mapProduto]:
        """Linha completa de todos os produtos ativos com preço > 0, sem limite —
        usado por get_Lista_de_Produtos."""
        sql = (
            f"SELECT {_COLUNAS_COMPLETAS} FROM tb_produto "
            "WHERE PRECO_BALCAO > 0.00 AND PRODUTO_ATIVO = 1 ORDER BY DESCRICAO_PRODUTO"
        )
        return db.query_all(sql, map_cls=mapProduto)

    def preco_delivery_por_id(self, id_produto: int) -> Optional[SimpleNamespace]:
        sql = "SELECT ID_PRODUTO, PRECO_DELIVERY FROM tb_produto WHERE ID_PRODUTO = %s"
        return db.query_one(sql, (id_produto,), map_cls=SimpleNamespace)

    def foto_por_id(self, id_produto: int) -> Optional[SimpleNamespace]:
        sql = "SELECT ID_PRODUTO, FOTO_PRODUTO FROM tb_produto WHERE ID_PRODUTO = %s"
        return db.query_one(sql, (id_produto,), map_cls=SimpleNamespace)

    def listar_para_venda(self) -> List[SimpleNamespace]:
        """Usado por getAllProducts — a query original do erro 500 relatado."""
        sql = (
            "SELECT ID_PRODUTO, CODIGO_PRODUTO, CODIGO_PRODUTO_PDV, DESCRICAO_PRODUTO, "
            "PRECO_BALCAO, PRECO_ATACADO, ID_TRIBUTO, CODIGO_ZE, PRODUTO_ATIVO, ID_FAMILIA "
            "FROM tb_produto WHERE PRECO_BALCAO > 0.00 AND PRODUTO_ATIVO = 1"
        )
        return db.query_all(sql, map_cls=SimpleNamespace)

    def listar_com_foto(self) -> List[SimpleNamespace]:
        sql = "SELECT ID_PRODUTO, FOTO_PRODUTO FROM tb_produto WHERE FOTO_PRODUTO IS NOT NULL"
        return db.query_all(sql, map_cls=SimpleNamespace)
