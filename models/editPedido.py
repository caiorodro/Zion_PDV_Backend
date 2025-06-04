from typing import List
from pydantic import BaseModel

class editItemPedido(BaseModel):
    NUMERO_ITEM: int
    NUMERO_PEDIDO: int
    ID_PRODUTO: int
    ID_TRIBUTO: int
    DESCRICAO_PRODUTO: str
    QTDE: int
    PRECO: float
    TOTAL: float

class editPedidoPagamento(BaseModel):
    ID_PAGAMENTO: int
    NUMERO_PEDIDO: int
    FORMA_PAGTO: str
    ID_CAIXA: int
    VALOR_PAGO: float
    CODIGO_NSU: str

class editPedido(BaseModel):
    NUMERO_PEDIDO: int
    ID_CLIENTE: int
    NOME_CLIENTE: str
    ID_TRANSPORTE: int
    NOME_TRANSPORTE: str
    ORIGEM: str
    TAXA_ENTREGA: float
    VALOR_ADICIONAL: float
    VALOR_DESCONTO: float
    INFO_ADICIONAL: str
    ID_CAIXA: int
    ITEMS: List[editItemPedido]
    PAGAMENTOS: List[editPedidoPagamento]
    ID_ENDERECO: int
