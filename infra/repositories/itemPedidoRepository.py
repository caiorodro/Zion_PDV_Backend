"""Acesso a dados da tabela tb_item_pedido.

Só o que já foi migrado até agora. O grosso é migrado junto com views/pedido.py.
"""

from types import SimpleNamespace
from typing import List

from infra import db
from base.mapTable import mapItemPedido
from models.itemPedido import itemPedido

_COLUNAS = (
    "NUMERO_ITEM, NUMERO_PEDIDO, ID_PRODUTO, CODIGO_PRODUTO, QTDE, PRECO_UNITARIO, VALOR_TOTAL, "
    "ID_TRIBUTO, OBS_ITEM, ID_ITEM_LOCAL, ID_TERMINAL"
)


class ItemPedidoRepository:
    def listar_por_pedido(self, numero_pedido: int, conn=None) -> List[mapItemPedido]:
        sql = f"SELECT {_COLUNAS} FROM tb_item_pedido WHERE NUMERO_PEDIDO = %s"
        if conn is not None:
            return db.query_all_in(conn, sql, (numero_pedido,), map_cls=mapItemPedido)
        return db.query_all(sql, (numero_pedido,), map_cls=mapItemPedido)

    def listar_com_produto(self, numero_pedido: int) -> List[SimpleNamespace]:
        """Itens do pedido com descrição/tributo/família do produto — usado
        por listaAtendimento()."""
        sql = (
            "SELECT ip.NUMERO_PEDIDO, ip.NUMERO_ITEM, ip.ID_PRODUTO, p.DESCRICAO_PRODUTO, "
            "ip.QTDE, ip.PRECO_UNITARIO, ip.VALOR_TOTAL, p.ID_TRIBUTO, p.ID_FAMILIA "
            "FROM tb_item_pedido ip INNER JOIN tb_produto p ON ip.ID_PRODUTO = p.ID_PRODUTO "
            "WHERE ip.NUMERO_PEDIDO = %s"
        )
        return db.query_all(sql, (numero_pedido,), map_cls=SimpleNamespace)

    def inserir(self, item: itemPedido, conn=None) -> int:
        sql = (
            "INSERT INTO tb_item_pedido (NUMERO_PEDIDO, ID_PRODUTO, CODIGO_PRODUTO, QTDE, "
            "PRECO_UNITARIO, VALOR_TOTAL, ID_TRIBUTO, OBS_ITEM, ID_ITEM_LOCAL, ID_TERMINAL) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            item.NUMERO_PEDIDO,
            item.ID_PRODUTO,
            item.CODIGO_PRODUTO,
            item.QTDE,
            item.PRECO_UNITARIO,
            item.VALOR_TOTAL,
            item.ID_TRIBUTO,
            item.OBS_ITEM,
            item.ID_ITEM_LOCAL,
            item.ID_TERMINAL,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def numero_pedido_do_item(self, numero_item: int) -> int:
        """Mesmo comportamento do código anterior: levanta IndexError se o
        item não existir (não engole o erro)."""
        sql = "SELECT NUMERO_PEDIDO FROM tb_item_pedido WHERE NUMERO_ITEM = %s"
        rows = db.query_all(sql, (numero_item,))
        return rows[0]["NUMERO_PEDIDO"]

    def deletar_por_numero_item(self, numero_item: int, conn=None) -> None:
        sql = "DELETE FROM tb_item_pedido WHERE NUMERO_ITEM = %s"
        if conn is not None:
            db.execute_in(conn, sql, (numero_item,))
        else:
            db.execute(sql, (numero_item,))

    def atualizar_tributo(self, numero_item: int, id_tributo: int) -> None:
        sql = "UPDATE tb_item_pedido SET ID_TRIBUTO = %s WHERE NUMERO_ITEM = %s"
        db.execute(sql, (id_tributo, numero_item))

    def deletar_por_item(self, numero_pedido: int, numero_item: int, conn=None) -> None:
        sql = "DELETE FROM tb_item_pedido WHERE NUMERO_PEDIDO = %s AND NUMERO_ITEM = %s"
        params = (numero_pedido, numero_item)
        if conn is not None:
            db.execute_in(conn, sql, params)
        else:
            db.execute(sql, params)
