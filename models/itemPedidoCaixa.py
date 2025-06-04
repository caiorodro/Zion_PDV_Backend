from pydantic import BaseModel

class itemPedidoCaixa(BaseModel):
    NUMERO_PEDIDO: int
    NUMERO_ITEM: int
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    QTDE: float
    PRECO: float
    TOTAL: float
    ID_TRIBUTO: int