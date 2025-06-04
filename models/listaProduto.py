from pydantic import BaseModel

class listaProduto(BaseModel):
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    PRECO_BALCAO: float
    ID_TRIBUTO: int
    SALDO: float
    CODIGO_ZE: str
