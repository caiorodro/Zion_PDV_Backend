from pydantic import BaseModel

class getProduto(BaseModel):
    ID_PRODUTO: int
    QTDE: int