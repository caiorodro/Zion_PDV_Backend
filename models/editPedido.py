from typing import List

from dataclasses import dataclass

@dataclass
class editItemPedido:
    NUMERO_ITEM: int
    NUMERO_PEDIDO: int
    ID_PRODUTO: int
    ID_TRIBUTO: int
    DESCRICAO_PRODUTO: str
    QTDE: int
    PRECO: float
    TOTAL: float

@dataclass
class editPedidoPagamento:
    ID_PAGAMENTO: int
    NUMERO_PEDIDO: int
    FORMA_PAGTO: str
    ID_CAIXA: int
    VALOR_PAGO: float
    CODIGO_NSU: str

@dataclass
class editPedido:
    NUMERO_PEDIDO: int
    ID_CLIENTE: int
    CPF: str
    NOME_CLIENTE: str
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str
    ORIGEM: str
    TOTAL_PRODUTOS: float
    TAXA_ENTREGA: float
    VALOR_ADICIONAL: float
    VALOR_DESCONTO: float
    VALOR_TOTAL: float
    VALOR_TROCO: float
    INFO_ADICIONAL: str
    ID_CAIXA: int
    ITEMS: List[editItemPedido]
    PAGAMENTOS: List[editPedidoPagamento]
    ID_ENDERECO: int
