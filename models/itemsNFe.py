from pydantic import BaseModel

class itemsNFe(BaseModel):
    NUMERO_ITEM: int
    DESCRICAO_PRODUTO: str
    QTDE: int
    PRECO: float
    TOTAL: float
    ID_TRIBUTO: int