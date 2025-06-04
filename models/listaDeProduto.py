from pydantic import BaseModel

class listaDeProduto(BaseModel):
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str
    PRECO_BALCAO: float
    ID_TRIBUTO: int