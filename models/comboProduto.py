from pydantic import BaseModel

class comboProduto(BaseModel):
    ID_PRODUTO: int
    DESCRICAO_PRODUTO: str