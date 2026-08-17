"""Acesso a dados de tb_pedido.

Só o que já foi migrado até agora (usado por views/cliente.py e views/caixa.py).
O grosso de tb_pedido — usado por views/pedido.py, com 120 queries e o fluxo
transacional de fechamento de venda — é migrado por último, no plano geral.
"""

from datetime import datetime
from types import SimpleNamespace
from typing import List, Optional

from infra import db
from base.mapTable import mapPedido

# Sentinela para distinguir "pedido não existe" de "pedido existe mas o CPF
# está vazio no banco" — o código anterior (via SQLAlchemy) fazia a mesma
# distinção (query vazia vs. .CPF is None).
PEDIDO_NAO_ENCONTRADO = object()

_COLUNAS = (
    "NUMERO_PEDIDO, DATA_HORA, DATA_ENTREGA, DATA_HORA_AGENDA, TEMPO_ENTREGA, TEMPO_RETIRADA_LOJA, "
    "TEMPO_MOTOBOY_CAMINHO, ID_CLIENTE, ID_ENDERECO, CPF, IE, NOME_CLIENTE, ENDERECO_CLIENTE, "
    "BAIRRO_CLIENTE, TELEFONE_CLIENTE, LATITUDE, LONGITUDE, ORIGEM, ID_CAIXA, STATUS_PEDIDO, "
    "NUMERO_PESSOAS, NUMERO_VENDA, TIPO_ADICIONAL, TOTAL_PRODUTOS, TROCO, DESCONTO, ADICIONAL, "
    "TAXA_ENTREGA, TOTAL_PEDIDO, MOTIVO_DEVOLUCAO, ID_TRANSPORTE, INFO_ADICIONAL, "
    "NUMERO_PEDIDO_ZE_DELIVERY, NUMERO_PEDIDO_DELIVERY, NUMERO_PEDIDO_LALAMOVE, NUMERO_PEDIDO_IFOOD, "
    "ID_PEDIDO_IFOOD, TIPO_PEDIDO_IFOOD, CODIGO_IDENTIFICACAO_IFOOD, ORDER_NUMBER_GOOMER, "
    "ID_PEDIDO_GOOMER, ORDER_NUMBER_WABIZ, INTERNAL_KEY_WABIZ, ORDER_NUMBER_RAPPI, "
    "REQUEST_ID_FATTORINO, INTERNAL_KEY_ZION, MOTIVO_CANCELAMENTO, COMENTARIOS_AVALIACAO, "
    "NOTA_AVALIACAO, ORDEM_ROTEIRO, TEMPO_ATENDIMENTO_ROBO, TEMPO_ENTREGA_PEDIDO, ID_PEDIDO_LOCAL, "
    "ID_TERMINAL"
)


_COLUNAS_INSERT = (
    "DATA_HORA, DATA_ENTREGA, DATA_HORA_AGENDA, TEMPO_ENTREGA, TEMPO_RETIRADA_LOJA, "
    "TEMPO_MOTOBOY_CAMINHO, ID_CLIENTE, ID_ENDERECO, CPF, IE, NOME_CLIENTE, ENDERECO_CLIENTE, "
    "BAIRRO_CLIENTE, TELEFONE_CLIENTE, LATITUDE, LONGITUDE, ORIGEM, ID_CAIXA, STATUS_PEDIDO, "
    "NUMERO_PESSOAS, NUMERO_VENDA, TIPO_ADICIONAL, TOTAL_PRODUTOS, TROCO, DESCONTO, ADICIONAL, "
    "TAXA_ENTREGA, TOTAL_PEDIDO, MOTIVO_DEVOLUCAO, ID_TRANSPORTE, INFO_ADICIONAL, "
    "NUMERO_PEDIDO_ZE_DELIVERY, NUMERO_PEDIDO_DELIVERY, NUMERO_PEDIDO_LALAMOVE, NUMERO_PEDIDO_IFOOD, "
    "ID_PEDIDO_IFOOD, TIPO_PEDIDO_IFOOD, CODIGO_IDENTIFICACAO_IFOOD, ORDER_NUMBER_GOOMER, "
    "ID_PEDIDO_GOOMER, ORDER_NUMBER_WABIZ, INTERNAL_KEY_WABIZ, ORDER_NUMBER_RAPPI, "
    "REQUEST_ID_FATTORINO, INTERNAL_KEY_ZION, MOTIVO_CANCELAMENTO, COMENTARIOS_AVALIACAO, "
    "NOTA_AVALIACAO, ORDEM_ROTEIRO, TEMPO_ATENDIMENTO_ROBO, TEMPO_ENTREGA_PEDIDO, ID_PEDIDO_LOCAL, "
    "ID_TERMINAL"
)
_PLACEHOLDERS_INSERT = ", ".join(["%s"] * len(_COLUNAS_INSERT.split(", ")))


class PedidoRepository:
    def buscar_por_numero(self, numero_pedido: int) -> Optional[mapPedido]:
        sql = f"SELECT {_COLUNAS} FROM tb_pedido WHERE NUMERO_PEDIDO = %s"
        return db.query_one(sql, (numero_pedido,), map_cls=mapPedido)

    def inserir(self, pedido, cliente, conn=None) -> int:
        """Grava o cabeçalho do pedido. `cliente` é um models.clientePedido.clientePedido
        (NOME_CLIENTE/ENDERECO/BAIRRO/TELEFONE vêm dele, não do próprio `pedido`
        — mesma escolha do código anterior, que sempre busca os dados atuais
        do cliente/endereço em vez de confiar no que veio no payload)."""
        sql = f"INSERT INTO tb_pedido ({_COLUNAS_INSERT}) VALUES ({_PLACEHOLDERS_INSERT})"
        params = (
            datetime.strptime(pedido.DATA_HORA, "%d/%m/%Y %H:%M"),
            datetime.strptime(pedido.DATA_ENTREGA, "%d/%m/%Y %H:%M"),
            datetime.strptime(pedido.DATA_HORA_AGENDA, "%d/%m/%Y %H:%M"),
            pedido.TEMPO_ENTREGA,
            datetime.strptime(pedido.TEMPO_RETIRADA_LOJA, "%d/%m/%Y %H:%M"),
            datetime.strptime(pedido.TEMPO_MOTOBOY_CAMINHO, "%d/%m/%Y %H:%M"),
            pedido.ID_CLIENTE,
            pedido.ID_ENDERECO,
            pedido.CPF,
            pedido.IE,
            cliente.NOME_CLIENTE,
            cliente.ENDERECO,
            cliente.BAIRRO,
            cliente.TELEFONE,
            pedido.LATITUDE,
            pedido.LONGITUDE,
            pedido.ORIGEM,
            pedido.ID_CAIXA,
            pedido.STATUS_PEDIDO,
            pedido.NUMERO_PESSOAS,
            pedido.NUMERO_VENDA,
            pedido.TIPO_ADICIONAL,
            pedido.TOTAL_PRODUTOS,
            pedido.TROCO,
            pedido.DESCONTO,
            pedido.ADICIONAL,
            pedido.TAXA_ENTREGA,
            pedido.TOTAL_PEDIDO,
            pedido.MOTIVO_DEVOLUCAO,
            pedido.ID_TRANSPORTE,
            pedido.INFO_ADICIONAL,
            pedido.NUMERO_PEDIDO_ZE_DELIVERY,
            pedido.NUMERO_PEDIDO_DELIVERY,
            pedido.NUMERO_PEDIDO_LALAMOVE,
            pedido.NUMERO_PEDIDO_IFOOD,
            pedido.ID_PEDIDO_IFOOD,
            pedido.TIPO_PEDIDO_IFOOD,
            pedido.CODIGO_IDENTIFICACAO_IFOOD,
            pedido.ORDER_NUMBER_GOOMER,
            pedido.ID_PEDIDO_GOOMER,
            pedido.ORDER_NUMBER_WABIZ,
            pedido.INTERNAL_KEY_WABIZ,
            pedido.ORDER_NUMBER_RAPPI,
            pedido.REQUEST_ID_FATTORINO,
            pedido.INTERNAL_KEY_ZION,
            pedido.MOTIVO_CANCELAMENTO,
            pedido.COMENTARIOS_AVALIACAO,
            pedido.NOTA_AVALIACAO,
            pedido.ORDEM_ROTEIRO,
            datetime.strptime(pedido.TEMPO_ATENDIMENTO_ROBO, "%d/%m/%Y %H:%M"),
            datetime.strptime(pedido.TEMPO_ENTREGA_PEDIDO, "%d/%m/%Y %H:%M"),
            pedido.ID_PEDIDO_LOCAL,
            pedido.ID_TERMINAL,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def soma_total_pedido_mes(self, id_cliente: int, inicio: datetime, fim: datetime, conn=None):
        """SUM(TOTAL_PEDIDO) de pedidos finalizados (status 3) do cliente no
        período — usado pelo limite mensal de vale funcionário."""
        sql = (
            "SELECT SUM(TOTAL_PEDIDO) AS TOTAL_VENDAS FROM tb_pedido "
            "WHERE ID_CLIENTE = %s AND DATA_HORA >= %s AND DATA_HORA < %s AND STATUS_PEDIDO = 3"
        )
        params = (id_cliente, inicio, fim)
        if conn is not None:
            row = db.query_one_in(conn, sql, params)
        else:
            row = db.query_one(sql, params)
        return row["TOTAL_VENDAS"] if row else None

    def cpf_por_numero_pedido(self, numero_pedido: int):
        sql = "SELECT CPF FROM tb_pedido WHERE NUMERO_PEDIDO = %s"
        row = db.query_one(sql, (numero_pedido,))
        return row["CPF"] if row else PEDIDO_NAO_ENCONTRADO

    def listar_periodo(self, inicio: datetime, fim: datetime, status: int) -> List[mapPedido]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_pedido "
            "WHERE DATA_HORA >= %s AND DATA_HORA < %s AND STATUS_PEDIDO = %s"
        )
        return db.query_all(sql, (inicio, fim, status), map_cls=mapPedido)

    def contar_por_status(self, id_caixa: int, status: int) -> List[SimpleNamespace]:
        sql = (
            "SELECT STATUS_PEDIDO, COUNT(NUMERO_PEDIDO) AS NUMERO_DE_PEDIDOS FROM tb_pedido "
            "WHERE ID_CAIXA = %s AND STATUS_PEDIDO = %s GROUP BY STATUS_PEDIDO"
        )
        return db.query_all(sql, (id_caixa, status), map_cls=SimpleNamespace)

    def troco_e_desconto_do_caixa(self, id_caixa: int, forma_pagto: str) -> SimpleNamespace:
        """SUM(TROCO)/SUM(DESCONTO) de tb_pedido, unidos com tb_pedido_pagamento
        filtrado por forma de pagamento — mesmo JOIN do código anterior
        (um pedido com mais de um pagamento na mesma forma soma em dobro;
        comportamento preservado, não corrigido aqui)."""
        sql = (
            "SELECT SUM(p.TROCO) AS TROCO, SUM(p.DESCONTO) AS DESCONTO "
            "FROM tb_pedido p INNER JOIN tb_pedido_pagamento pg ON p.NUMERO_PEDIDO = pg.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s AND pg.FORMA_PAGTO = %s"
        )
        return db.query_one(sql, (id_caixa, forma_pagto), map_cls=SimpleNamespace)

    def somar_troco_do_caixa(self, id_caixa: int):
        """SUM(TROCO) sem join — usado por calculaCaixaPorFormaPagto."""
        sql = "SELECT SUM(TROCO) AS TROCO FROM tb_pedido WHERE STATUS_PEDIDO = 3 AND ID_CAIXA = %s"
        row = db.query_one(sql, (id_caixa,))
        return row["TROCO"] if row else None

    def somar_troco_do_caixa_com_join_pagamento(self, id_caixa: int):
        """SUM(TROCO) unido com tb_pedido_pagamento — usado por
        get_Total_Geral_Caixa. Mesma ressalva do join em troco_e_desconto_do_caixa."""
        sql = (
            "SELECT SUM(p.TROCO) AS TROCO FROM tb_pedido p "
            "INNER JOIN tb_pedido_pagamento pg ON p.NUMERO_PEDIDO = pg.NUMERO_PEDIDO "
            "WHERE p.STATUS_PEDIDO = 3 AND p.ID_CAIXA = %s"
        )
        row = db.query_one(sql, (id_caixa,))
        return row["TROCO"] if row else None

    def somar_troco_por_origem(self, id_caixa: int, origem: str):
        sql = (
            "SELECT SUM(TROCO) AS TROCO FROM tb_pedido "
            "WHERE STATUS_PEDIDO = 3 AND ID_CAIXA = %s AND ORIGEM = %s"
        )
        row = db.query_one(sql, (id_caixa, origem))
        return row["TROCO"] if row else None

    # -- listagem de pedidos (tela de busca) -------------------------------
    # Todo parametrizado — a versão anterior (SQLAlchemy `text()`) montava o
    # SQL com f-string, incluindo o texto de busca do usuário direto na
    # query (injeção de SQL). Corrigido aqui.

    _COLUNAS_LISTAGEM = (
        "pg.NUMERO_PEDIDO, pg.DATA_HORA, p.STATUS_PEDIDO, p.NOME_CLIENTE, p.TOTAL_PEDIDO, "
        "p.ORIGEM, p.ID_TRANSPORTE, t.NOME_TRANSPORTE, p.ID_CLIENTE, p.NUMERO_PEDIDO_IFOOD, "
        "p.ENDERECO_CLIENTE, p.TELEFONE_CLIENTE, pg.FORMA_PAGTO, pg.VALOR_PAGO, pg.CODIGO_NSU, "
        "pg.ID_PAGAMENTO, "
        "CASE WHEN EXISTS (SELECT 1 FROM tb_pedido_nfe pnf WHERE pnf.NUMERO_PEDIDO = pg.NUMERO_PEDIDO "
        "AND pnf.PROCESSADO = 10) THEN 1 ELSE 0 END AS nota"
    )
    _FROM_LISTAGEM = (
        "FROM tb_pedido p "
        "JOIN tb_pedido_pagamento pg ON pg.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
        "LEFT JOIN tb_transporte t ON t.ID_TRANSPORTE = p.ID_TRANSPORTE"
    )

    def listar_por_numero(self, numero_pedido) -> List[SimpleNamespace]:
        sql = f"SELECT {self._COLUNAS_LISTAGEM} {self._FROM_LISTAGEM} WHERE p.NUMERO_PEDIDO = %s"
        return db.query_all(sql, (numero_pedido,), map_cls=SimpleNamespace)

    def listar_por_numero_ze(self, numero_ze) -> List[SimpleNamespace]:
        sql = f"SELECT {self._COLUNAS_LISTAGEM} {self._FROM_LISTAGEM} WHERE p.NUMERO_PEDIDO_ZE_DELIVERY = %s"
        return db.query_all(sql, (numero_ze,), map_cls=SimpleNamespace)

    def listar_por_numero_ifood(self, numero_ifood) -> List[SimpleNamespace]:
        sql = f"SELECT {self._COLUNAS_LISTAGEM} {self._FROM_LISTAGEM} WHERE p.NUMERO_PEDIDO_IFOOD = %s"
        return db.query_all(sql, (numero_ifood,), map_cls=SimpleNamespace)

    def listar_por_periodo(
        self,
        inicio: datetime,
        fim: datetime,
        nome_filtro: str,
        origem: str,
        status_list: List[int],
        offset: int,
        limite: int = 50,
    ) -> List[SimpleNamespace]:
        sql = f"SELECT {self._COLUNAS_LISTAGEM} {self._FROM_LISTAGEM} WHERE (p.DATA_HORA >= %s AND p.DATA_HORA < %s)"
        params: list = [inicio, fim]

        if nome_filtro:
            sql += " AND p.NOME_CLIENTE LIKE %s"
            params.append(f"%{nome_filtro}%")

        if origem != "Todos":
            sql += " AND p.ORIGEM = %s"
            params.append(origem)

        if 0 not in status_list:
            placeholders = ", ".join(["%s"] * len(status_list))
            sql += f" AND p.STATUS_PEDIDO IN ({placeholders})"
            params.extend(status_list)

        sql += " ORDER BY p.DATA_HORA DESC LIMIT %s OFFSET %s"
        params.extend([limite, offset])

        return db.query_all(sql, tuple(params), map_cls=SimpleNamespace)

    # -- edição de pedido ---------------------------------------------------

    def buscar_resumo_edicao(self, numero_pedido: int) -> Optional[SimpleNamespace]:
        sql = (
            "SELECT NUMERO_PEDIDO, CPF, ID_CLIENTE, ID_ENDERECO, NOME_CLIENTE, ID_TRANSPORTE, "
            "ID_CAIXA, ORIGEM, TAXA_ENTREGA, ADICIONAL, DESCONTO, TOTAL_PRODUTOS, TOTAL_PEDIDO, "
            "TROCO, INFO_ADICIONAL FROM tb_pedido WHERE NUMERO_PEDIDO = %s"
        )
        return db.query_one(sql, (numero_pedido,), map_cls=SimpleNamespace)

    def atualizar_status(self, numero_pedido: int, status: int, conn=None) -> None:
        sql = "UPDATE tb_pedido SET STATUS_PEDIDO = %s WHERE NUMERO_PEDIDO = %s"
        params = (status, numero_pedido)
        if conn is not None:
            db.execute_in(conn, sql, params)
        else:
            db.execute(sql, params)

    def atualizar_dados_edicao(
        self,
        numero_pedido: int,
        id_cliente: int,
        nome_cliente: str,
        id_endereco: int,
        endereco_cliente: str,
        bairro_cliente: str,
        id_transporte: int,
        total_produtos: float,
        taxa_entrega: float,
        adicional: float,
        desconto: float,
        info_adicional: str,
        total_pedido: float,
        troco: float,
    ) -> None:
        sql = (
            "UPDATE tb_pedido SET ID_CLIENTE = %s, NOME_CLIENTE = %s, ID_ENDERECO = %s, "
            "ENDERECO_CLIENTE = %s, BAIRRO_CLIENTE = %s, ID_TRANSPORTE = %s, TOTAL_PRODUTOS = %s, "
            "TAXA_ENTREGA = %s, ADICIONAL = %s, DESCONTO = %s, INFO_ADICIONAL = %s, "
            "TOTAL_PEDIDO = %s, TROCO = %s WHERE NUMERO_PEDIDO = %s"
        )
        params = (
            id_cliente, nome_cliente, id_endereco, endereco_cliente, bairro_cliente,
            id_transporte, total_produtos, taxa_entrega, adicional, desconto,
            info_adicional, total_pedido, troco, numero_pedido,
        )
        db.execute(sql, params)

    def atualizar_totais(self, numero_pedido: int, total_produtos: float, total_pedido: float, troco: float) -> None:
        sql = (
            "UPDATE tb_pedido SET TOTAL_PRODUTOS = %s, TOTAL_PEDIDO = %s, TROCO = %s "
            "WHERE NUMERO_PEDIDO = %s"
        )
        db.execute(sql, (total_produtos, total_pedido, troco, numero_pedido))

    def listar_candidatos_faturamento(
        self, primeiro_dia_mes: datetime, origens: Optional[List[str]] = None
    ) -> List[mapPedido]:
        """Pedidos finalizados (status 3) do mês corrente, ainda sem NFC-e
        autorizada — usado pelo bot de faturamento automático."""
        sql = (
            f"SELECT {_COLUNAS} FROM tb_pedido p "
            "WHERE p.STATUS_PEDIDO = 3 AND p.DATA_HORA >= %s "
            "AND p.NUMERO_PEDIDO NOT IN (SELECT NUMERO_PEDIDO FROM tb_pedido_nfe WHERE PROCESSADO = 10)"
        )
        params: list = [primeiro_dia_mes]

        if origens:
            placeholders = ", ".join(["%s"] * len(origens))
            sql += f" AND p.ORIGEM IN ({placeholders})"
            params.extend(origens)

        sql += " ORDER BY p.DATA_HORA ASC"

        return db.query_all(sql, tuple(params), map_cls=mapPedido)

    def somar_faturado_no_mes(self, primeiro_dia_mes: datetime):
        sql = (
            "SELECT SUM(p.TOTAL_PEDIDO) AS TOTAL FROM tb_pedido p "
            "INNER JOIN tb_pedido_nfe pnf ON pnf.NUMERO_PEDIDO = p.NUMERO_PEDIDO "
            "WHERE pnf.PROCESSADO = 10 AND p.DATA_HORA >= %s"
        )
        row = db.query_one(sql, (primeiro_dia_mes,))
        return row["TOTAL"] if row else None

    def buscar_por_numeros(self, numeros: List[int]) -> List[mapPedido]:
        if not numeros:
            return []
        placeholders = ", ".join(["%s"] * len(numeros))
        sql = f"SELECT {_COLUNAS} FROM tb_pedido WHERE NUMERO_PEDIDO IN ({placeholders})"
        return db.query_all(sql, tuple(numeros), map_cls=mapPedido)

    def atualizar_cpf(self, numero_pedido: int, cpf: str) -> None:
        sql = "UPDATE tb_pedido SET CPF = %s WHERE NUMERO_PEDIDO = %s"
        db.execute(sql, (cpf, numero_pedido))

    def buscar_cliente_e_total(self, numero_pedido: int) -> Optional[SimpleNamespace]:
        sql = (
            "SELECT p.NUMERO_PEDIDO, p.ID_CLIENTE, c.NOME_CLIENTE, p.TOTAL_PEDIDO "
            "FROM tb_pedido p INNER JOIN tb_cliente c ON p.ID_CLIENTE = c.ID_CLIENTE "
            "WHERE p.NUMERO_PEDIDO = %s LIMIT 1"
        )
        return db.query_one(sql, (numero_pedido,), map_cls=SimpleNamespace)
