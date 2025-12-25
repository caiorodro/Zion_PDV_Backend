from dataclasses import dataclass

@dataclass
class itemPedidoCaixa:
    NUMERO_PEDIDO: int
    NUMERO_ITEM: int
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    QTDE: float
    PRECO: float
    TOTAL: float
    ID_TRIBUTO: int
    QTDE_FRACIONADA: bool