from pydantic import BaseModel

class itemPedido(BaseModel):
    NUMERO_ITEM: int
    NUMERO_PEDIDO: int
    ID_PRODUTO: int
    CODIGO_PRODUTO: str
    QTDE: int
    PRECO_UNITARIO: float
    VALOR_TOTAL: float
    ID_TRIBUTO: int
    OBS_ITEM: str
    ID_ITEM_LOCAL: int
    ID_TERMINAL: int
